from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Max
from django.utils import timezone
from chat_analyzer.models import Conversation, UnmatchedMessage, UploadHistory
from chat_analyzer.services.text_cleaner import clean_text
import re
import os
from datetime import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Upload Whatsapp chat files and process them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dir',
            type=str,
            default='chat_analyzer/fixtures/sample_chats/',
            help='Directory containing .txt chat files'
        )
        parser.add_argument(
            '--uploader',
            type=str,
            default='admin1',
            help='Username of the person uploading it can be wether (admin or therapist)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
        parser.add_argument(
            '--files',
            nargs='+',
            help='Specific files to upload (e.g., --files file1.txt file2.txt)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of files to process'
        )

        def handle(self, *args, **options):
            chat_dir = options['dir']
            uploader_username = options['uploader']
            verbose = options.get('verbose', False)
            specific_files = options.get('files')
            limit = options.get('limit')

            # get the uploader user (Admin or Therapist)
            try:
                uploader = User.objects.get(username=uploader_username)

            excepts User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User "{uploader_username}" not found !'))
                for user in User.objects.all():
                    self.stdout.write(f'   - {user.username} ({user.role})')
                return

            self.stdout.write(self.style.SUCCESS('\n WHATSAPP CHAT UPLOAD \n'))
            self.stdout.write('=' * 70)
            self.stdout.write(f'\n Uploader: {uploader.username} ({uploader.role})')

            # check if Directory exist or not we use os libaries to do it
            if not os.path.exists(chat_dir):
                self.stdout.write(self.style.ERROR(f'❌ Directory not found: {chat_dir}'))
                return

            # get all .txt files if specific_files exist
            if specific_files:
                txt_files = [f for f in specific_files if f.endswith('.txt')]

                if not txt_files:
                    self.stdout.write(self.style.ERROR('❌ No .txt files specified! '))

                    return

            else:
                txt_files = [f for f in os.listdir(chat_dir) if f.endswith('.txt')]

            if not txt_files:
                self.stdout.write(self.style.ERROR('❌ No .txt files found !'))

            # apply da limit if specified
            if limit and len(txt_files) > limit:
                txt_files = txt_files[:limit]

            self.stdout.write(f'\n Found {len(txt_files)} chat files:\n')
            for f in text_files:
                self.stdout.write(f' {f}')

            # declaring the temporary variable
            total_matched = 0
            total_unmatched = 0
            total_messages = 0
            total_duplicates = 0

            # get latest dates per client + chat type for deduplication
            latest_dates = self.get_latest_dates_per_client_per_type()

            for filename in txt_files:
                filepath = os.path.join(chat_dir, filename)
                self.stdout.write(f'\n 🧲 Processing: {filename}')

                try: 
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌Error reading file: {e}'))
                    continue

                # create upload history
                upload = UploadHistory.objects.create(
                    uploaded_by = uploader,
                    file_name=filename,
                    status='processing'
)

                lines = content.split('\n')
                matched_count = 0
                unmatched_count = 0
                duplicate_count = 0

                for line in lines:
                    if not line.strip():
                        continue

                    # parse Whatsapp format: [12/08/24, 10:30:45] +
                    match = re.match(r'\[(.*?)\]s(.*?):\s(.*)', line)
                    if not match:
                        if verbose:
                            self.stdout.write(f'❌ Skipped: {line[:30]}...')
                        continue

                    timestamp = match.group(1).strip()
                    sender = match.group(2).strip()
                    message = match.group(3).strip()

                    # clean the message import the method from services
                    cleaned = clean_text(message)

                    # try to match sender to a client, extract_phone ? 
                    phone = self.extract_phone(sender)
                    client = None
                    
                    if phone:
                        client = User.objects.filter(phone=phone, role='client').first()
                        if not client:
                            # try without country code
                            local_phone = phone.replace('+60', '0')
                            # then we find wether it have that number phone or not 
                            client = User.objects.filter(phone=local_phone, role='client').first()

                        if client:
                            # ✅ matched 
                            date = self.parse_date(timestamp)
                            time = self.parse_time(timestamp)

                            # ✅ detect chat type from filename
                            chat_type = self.detect_chat_type(filename)

                            # ✅ Check if this is a new message ( per client per chat type )
                            latest_date = latest_dates.get((client.id, chat_type))

                            if latest_date and date <= latest_date:
                                # here we skip old message to avoid the duplicates
                                duplicate_count += 1
                                if verbose:
                                    self.stdout.write(f'    ⏭️ Skipping old {chat_type} chat for {client.username}({date} <= {latest_date})'
                                continue
                            
                            # ✅ Generate message hash for deduplication
                            import hashlib
                            text_hash = f"{client.id}{date}{time}{sender}{message}"
                            message_hash = hashlib.sha256(text_hash.encode()).hexdigest()

                            # ✅ Check exact duplicate just in case to make it super accurate
                            existing = Conversation.objects.filter(
                             client=client,
                                message_hash=message_hash
                            ).first()

                            if existing:
                                duplicate_count += 1
                                if verbose:
                                    self.stdout.write(f'  duplicate message for {client.username}')
                                continue

                            # than we can create the conversation
                            Conversation.objects.create(
                                client=client,
                                date=date,
                                time=time,
                                username=sender,
                                message=message,
                                cleaned_text=cleaned,
                                chat_type=chat_type,
                                uploaded_by=uploader,
                                upload_history=upload,
                                upload_batch=upload.batch_id,
                                message_hash=message_hash
                            )
                            matched_count += 1

                            # then we can update the latest date for this client
                            latest_dates[(client.id, chat_type)] = date

                            if verbose:
                                self.stdout.write(f'    {chat_type} chat: {client.username} ({date})')

                        else:
                            # UNMATCHED
                            UnmatchedMessage.objects.create(
                                upload_history=upload,
                                date=self.parse_date(timestamp),
                                time=self.parse_time(timestamp),
                                username=sender,
                                message=message,
                                upload_batch=upload.batch_id
                            )
                            unmatched_count += 1
                            if verbose:
                                self.stdout.write(f'   Unmatched: {sender})
                                
                    # update uploadhistory
                    upload.message_count = matched_count + unmatched_count + duplicate_count
                    upload.matched_count = matched_count
                    upload.unmatched_count = unmatched_count
                    upload.duplicate_count = duplicate_count
                    upload.status = 'success' if matched_count > 0 else 'partial'
                    upload.save()

                    total_matched += matched_count
                    total_unmatched += unmatched_count
                    total_messages += matched_count + unmatched_count + duplicate_count
                    total_duplicates += duplicate_count

                    self.stdout.write(f'    {filename}: {matched_count} matched, {unmatched_count} unmatched, {duplicate_count} duplicates')

                # and then we can shows the summary
                # Show summary
self.stdout.write(self.style.SUCCESS('\n📊 UPLOAD SUMMARY\n'))
                self.stdout.write('=' * 60)
                self.stdout.write(f'\n👤 Uploaded by: {uploader.username} ({uploader.role})')
                self.stdout.write(f'📁 Total Files: {len(txt_files)}')
                self.stdout.write(f'📝 Total Messages: {total_messages}')
                self.stdout.write(f'✅ Matched: {total_matched}')
                self.stdout.write(f'❌ Unmatched: {total_unmatched}')
                self.stdout.write(f'⏭️ Duplicates Skipped: {total_duplicates}')
                if total_messages > 0:
                    self.stdout.write(f'📊 Match Rate: {total_matched/total_messages*100:.1f}%')

                self.stdout.write(self.style.SUCCESS('\n✅ Upload complete!'))

            # ===============================================
            # HELPER METHODS SECTION
            # ===============================================

            def extract_phone(self, text):
                """extract phone number from sender"""
                match = re.search(r'(\+?\d{10,15})', text)
                return match.group(0) if match else None

            def parse_date(self, timestamp):
                """parse the date from the timestamp"""
                try:
                    date_part = timestamp.split(',')[0].strip()
                    return datetime.strptime(date_part, '%d/%m/%y').date()
                except:
                    return datetime.now().date()

            def detect_chat_type(self, filename):
                """detect chat type from filename"""
                filename_lower = filename.lower()
                if 'group' in filename_lower:
                    return 'group'
                elif 'admin' in filename_lower:
                    return 'admin'
                else:
                    return 'individual'

            def get_latest_dates_per_client_per_type(self):
                latest = Conversation.objects.values('client', 'chat_type').annotate(
                    latest_date=Max('date')
                )
                return {
                    (item['client'], item['chat_type']): item['latest_date']
                    for item in latest
                    if item['client'] is not None and item['chat_type'] is not None
                }

                        





        
