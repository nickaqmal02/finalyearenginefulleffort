# chat_analyzer/management/commands/upload_chats.py
import hashlib
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from chat_analyzer.models import Conversation, UploadHistory, UnmatchedMessage, User
from chat_analyzer.services.text_cleaner import get_cleaner
from chat_analyzer.services.whatsapp_parser import parse_whatsapp_file

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Upload chat messages from a file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            required=True,
            help='Path to the chat file'
        )
        parser.add_argument(
            '--client-id',
            type=int,
            required=True,
            help='Client ID to associate messages with'
        )
        parser.add_argument(
            '--uploader-id',
            type=int,
            help='User ID of the person uploading (default: admin)'
        )
        parser.add_argument(
            '--batch-id',
            type=str,
            help='Custom batch ID (optional)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Parse file without saving to database'
        )
        parser.add_argument(
            '--clean-only',
            action='store_true',
            help='Only clean messages without uploading'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        client_id = options['client_id']
        uploader_id = options.get('uploader_id')
        batch_id = options.get('batch_id')
        dry_run = options.get('dry_run', False)
        clean_only = options.get('clean_only', False)

        self.stdout.write(self.style.SUCCESS('\n📤 UPLOADING CHATS\n'))
        self.stdout.write('=' * 60)

        # Get the client
        try:
            client = User.objects.get(id=client_id, role='client')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ Client with ID {client_id} not found'))
            return

        # Get uploader
        uploader = None
        if uploader_id:
            try:
                uploader = User.objects.get(id=uploader_id)
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'⚠️ Uploader with ID {uploader_id} not found, using admin'))

        # Get cleaner
        cleaner = get_cleaner()

        # Parse the chat file using our whatsapp parser services
        try:
            messages = parse_whatsapp_file(file_path)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'❌ File not found: {file_path}'))
            return
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error parsing file: {e}'))
            return

        if not messages:
            self.stdout.write(self.style.ERROR('❌ No messages found in file'))
            return

        self.stdout.write(f'📊 Found {len(messages)} messages in file')

        # If clean-only, just clean and show sample
        if clean_only:
            self.stdout.write('\n🧹 Cleaning messages...')
            cleaned_messages = []
            for msg in messages:
                cleaned_sentiment = cleaner.clean_for_sentiment(msg['message'])
                cleaned_topic = cleaner.clean_for_topic_modeling(msg['message'])
                cleaned_messages.append({
                    **msg,
                    'cleaned_sentiment': cleaned_sentiment,
                    'cleaned_topic': cleaned_topic
                })
            
            # Show sample
            self.stdout.write('\n📝 Sample cleaning:')
            for i, msg in enumerate(cleaned_messages[:3]):
                self.stdout.write(f'\n{i+1}. Original: {msg["message"][:80]}...')
                self.stdout.write(f'   Sentiment: {msg["cleaned_sentiment"][:80]}...')
                self.stdout.write(f'   Topic:     {msg["cleaned_topic"][:80]}...')
            
            self.stdout.write(self.style.SUCCESS('\n✅ Cleaning preview complete'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️ DRY RUN - No data will be saved'))
            self.stdout.write('📝 First 5 messages:')
            for msg in messages[:5]:
                self.stdout.write(f'   {msg["date"]} - {msg["username"]}: {msg["message"][:50]}...')
            return

        # Process and save messages
        with transaction.atomic():
            # Create upload history
            upload_history = UploadHistory.objects.create(
                uploaded_by=uploader,
                file_name=file_path.split('/')[-1],
                batch_id=batch_id,
                status='processing'
            )

            self.stdout.write('\n💾 Saving messages to database...')

            saved_count = 0
            duplicate_count = 0
            unmatched_count = 0
            positive_count = 0
            negative_count = 0
            neutral_count = 0

            for msg in messages:
                # Create message hash for deduplication
                text = f"{client_id}{msg['date']}{msg['username']}{msg['message']}"
                message_hash = hashlib.sha256(text.encode()).hexdigest()

                # Check for duplicate
                if Conversation.objects.filter(message_hash=message_hash).exists():
                    duplicate_count += 1
                    continue

                # Clean the message for both purposes
                cleaned_sentiment = cleaner.clean_for_sentiment(msg['message'])
                cleaned_topic = cleaner.clean_for_topic_modeling(msg['message'])

                # Create conversation
                conversation = Conversation(
                    client=client,
                    date=msg['date'],
                    time=msg['time'],
                    username=msg['username'],
                    message=msg['message'],
                    cleaned_text=cleaned_sentiment,          # For sentiment analysis
                    cleaned_text_topic=cleaned_topic,        # For topic modeling
                    is_cleaned_sentiment=True,               # Mark as cleaned for sentiment
                    is_cleaned_topic=True,                   # Mark as cleaned for topic modeling
                    message_hash=message_hash,
                    upload_batch=upload_history.batch_id,
                    upload_history=upload_history,
                    uploaded_by=uploader,
                    uploaded_at=datetime.now(),
                    is_processed=False,
                    chat_type='individual'
                )

                # Try to find sender (could be client or therapist)
                # For now, set sender as client if username matches client name
                # Otherwise try to find therapist by name
                sender = self.find_sender(msg['username'], client)
                if sender:
                    conversation.sender = sender
                    conversation.is_from_client = (sender.id == client.id)
                else:
                    # If sender not found, this is an unmatched message
                    unmatched_count += 1
                    # We'll still save the conversation but without sender

                try:
                    conversation.save()
                    saved_count += 1

                    # Update sentiment counts (placeholder - will be updated by sentiment analyzer)
                    # For now, just count neutral
                    neutral_count += 1

                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Error saving message: {e}'))
                    continue

                # Progress indicator
                if saved_count % 100 == 0:
                    self.stdout.write(f'   Saved {saved_count} messages...')

            # Update upload history
            upload_history.message_count = saved_count + duplicate_count
            upload_history.matched_count = saved_count
            upload_history.unmatched_count = unmatched_count
            upload_history.duplicate_count = duplicate_count
            upload_history.positive_count = positive_count
            upload_history.negative_count = negative_count
            upload_history.neutral_count = neutral_count
            upload_history.status = 'success'
            upload_history.save()

        # Final summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ UPLOAD COMPLETE'))
        self.stdout.write('=' * 60)
        self.stdout.write(f'📊 Total messages processed: {len(messages)}')
        self.stdout.write(f'   ✅ Saved: {saved_count}')
        self.stdout.write(f'   🔄 Duplicates: {duplicate_count}')
        self.stdout.write(f'   ❌ Unmatched senders: {unmatched_count}')
        self.stdout.write(f'   📁 Batch ID: {upload_history.batch_id}')
        self.stdout.write('\n📝 Cleaning statistics:')
        self.stdout.write(f'   🧹 All messages cleaned for sentiment analysis')
        self.stdout.write(f'   🧹 All messages cleaned for topic modeling')
        self.stdout.write('\n💡 Next steps:')
        self.stdout.write('   1. Run sentiment analysis: python manage.py analyze_sentiment')
        self.stdout.write('   2. Train topic model: python manage.py train_topics')
        self.stdout.write('=' * 60)

    def _normalize(self, value):
        """Normalize a name/phone for comparison: lowercase, strip ~, emoji, symbols."""
        if not value:
            return ""
        value = value.lower()
        # keep only letters and digit
        value = "".join(ch for ch in value if ch.isalnum())
        return value

    def find_sender(self, username, client):
        """
        Match a WhatsApp sender to User, in priority order:
        1. Phone number (can come from User.phone or any ClientContact.phone_number)
        2. Full name (client's names or any parent contact name)
        3. Substring (Sender name appears inside a user's full name)
        """
        from chat_analyzer.models import User, ClientContact

        sender_key = self._normalize(username)
        if not sender_key:
            return None

        # 1. kito match by phone number 
        phone_to_user = {}
        for u in User.objects.filter(phone__isnull=False).exclude(phone=""):
            key = self._normalize(u.phone)
            if key:
                phone_to_user[key] = u
        
        # also collect clientcontact phone 
        for contact in ClientContact.objects.select_related("client"):
            key = self._normalize(contact.phone_number)
            if key:
                phone_to_user[key] = contact.client

        if sender_key in phone_to_user:
            return phone_to_user[sender_key]

        # 2. we check by full name
        client_key = self._normalize(
            (client.first_name or "") + (client.last_name or "")
        )
        if client_key and sender_key == client_key:
            return client

        # we also check parent contact name
        contacts = ClientContact.objects.filter(client=client)
        for contact in contacts:
            if sender_key == self._normalize(contact.name):
                return client

        # 3. -- we match by substring -- (sender name inside a full name )
        # e.g. sender ~Fauzi should match client Fauzi Amirah
        if client_key and (sender_key in client_key or client_key in sender_key):
            return client
        for contact in contacts:
            ckey = self._normalize(contact.name)
            if ckey and (sender_key in ckey or ckey in sender_key):
                return client

        # therapist / doctor by full name
        for staff in User.objects.filter(role__in=["therapist", "doctor"]):
            staff_key = self._normalize(
                (staff.first_name or "") + (staff.last_name or "")
            )
            if staff_key and (sender_key == staff_key or sender_key in staff_key):
                return staff 
        # if no match
        return None

