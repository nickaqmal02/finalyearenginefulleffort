# chat_analyzer/management/commands/upload_chats.py
import logging
from django.core.management.base import BaseCommand
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
        # === THIN WRAPPER — delegates to process_whatsapp_upload ===
        # All business logic lives in upload_service.py
        # This function only handles CLI output

        # handle clean-only as a separate pre-check (service doesn't support it)
        if options.get('clean_only'):
            try:
                messages = parse_whatsapp_file(options['file'])
            except FileNotFoundError:
                self.stdout.write(self.style.ERROR(f'❌ File not found: {options["file"]}'))
                return

            cleaner = get_cleaner()
            self.stdout.write(self.style.SUCCESS('\n🧹 CLEANING PREVIEW\n'))
            self.stdout.write('=' * 60)
            for i, msg in enumerate(messages[:3], 1):
                cleaned_s = cleaner.clean_for_sentiment(msg['message'])
                cleaned_t = cleaner.clean_for_topic_modeling(msg['message'])
                self.stdout.write(f'\n{i}. Original: {msg["message"][:80]}...')
                self.stdout.write(f'   Sentiment: {cleaned_s[:80]}...')
                self.stdout.write(f'   Topic:     {cleaned_t[:80]}...')
            self.stdout.write(self.style.SUCCESS('\n✅ Cleaning preview complete'))
            return

        # call the service — pass through all args
        from chat_analyzer.services.upload_service import process_whatsapp_upload

        result = process_whatsapp_upload(
            file_path_or_file=options['file'],
            client_id=options['client_id'],
            uploader_id=options.get('uploader_id'),
            batch_id=options.get('batch_id'),
            dry_run=options.get('dry_run', False),
        )

        # === CLI output formatting only ===
        self.stdout.write(self.style.SUCCESS('\n📤 UPLOAD CHATS\n'))
        self.stdout.write('=' * 60)

        if result.get('error'):
            self.stdout.write(self.style.ERROR(f"❌ {result['error']}"))
            return

        if result.get('dry_run'):
            self.stdout.write(self.style.WARNING('\n⚠️ DRY RUN'))
            self.stdout.write(f'📊 {result["message_count"]} messages would be imported')
            return

        # success — print summary
        self.stdout.write(self.style.SUCCESS('✅ UPLOAD COMPLETE'))
        self.stdout.write(f'📊 Total processed: {result["total"]}')
        self.stdout.write(f'   ✅ Saved: {result["saved"]}')
        self.stdout.write(f'   🔄 Duplicates: {result["duplicates"]}')
        self.stdout.write(f'   ❌ Unmatched senders: {result["unmatched"]}')
        self.stdout.write(f'   📁 Batch ID: {result["batch_id"]}')
        self.stdout.write('')
        self.stdout.write('📝 Sentiment breakdown:')
        self.stdout.write(f'   🟢 Positive: {result["positive"]}')
        self.stdout.write(f'   🔴 Negative: {result["negative"]}')
        self.stdout.write(f'   ⚪ Neutral:  {result["neutral"]}')
        self.stdout.write('')
        self.stdout.write('💡 Next steps:')
        self.stdout.write('   1. Run topic training: python manage.py train_topics')
        self.stdout.write('   2. View in admin: /admin/chat_analyzer/conversation/')
        self.stdout.write('=' * 60)