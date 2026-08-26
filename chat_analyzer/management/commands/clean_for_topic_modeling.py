# chat_analyzer/management/commands/clean_for_topic_modeling.py
from django.core.management.base import BaseCommand
from chat_analyzer.services.text_cleaner import batch_clean_conversations

class Command(BaseCommand):
    help = 'Clean existing conversations for topic modeling'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of messages to clean'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-cleaning even if already cleaned'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        force = options.get('force', False)

        self.stdout.write(self.style.SUCCESS('\n🧹 CLEANING MESSAGES FOR TOPIC MODELING\n'))
        self.stdout.write('=' * 60)

        # Get messages that need cleaning
        from chat_analyzer.models import Conversation
        
        if force:
            # Force re-clean all messages
            conversations = Conversation.objects.all()
        else:
            # Only clean messages that haven't been cleaned for topic modeling
            conversations = Conversation.objects.filter(
                is_cleaned_topic=False
            )

        if limit:
            conversations = conversations[:limit]

        total = conversations.count()

        if total == 0:
            if force:
                self.stdout.write('ℹ️ No conversations found to clean')
            else:
                self.stdout.write('✅ All messages are already cleaned for topic modeling')
                self.stdout.write('   Use --force to re-clean all messages')
            return

        self.stdout.write(f'📊 Found {total} conversations to clean')

        # Clean the messages
        from chat_analyzer.services.text_cleaner import get_cleaner
        cleaner = get_cleaner()
        
        cleaned_count = 0
        for conv in conversations:
            if force or not conv.is_cleaned_topic:
                conv.cleaned_text_topic = cleaner.clean_for_topic_modeling(conv.message)
                conv.is_cleaned_topic = True
                conv.save()
                cleaned_count += 1
                
                if cleaned_count % 100 == 0:
                    self.stdout.write(f'   Cleaned {cleaned_count} messages...')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully cleaned {cleaned_count} messages for topic modeling'))

        # Show sample
        sample = Conversation.objects.filter(is_cleaned_topic=True).first()
        if sample:
            self.stdout.write('\n📝 Sample cleaning:')
            self.stdout.write(f'   Original: {sample.message[:100]}...')
            self.stdout.write(f'   Cleaned:  {sample.cleaned_text_topic[:100]}...')
