from django.core.management.base import BaseCommand
from chat_analyzer.models import Conversation
from chat_analyzer.services.text_cleaner import clean_text
from chat_analyzer.services.sentiment_analyzer import analyze_sentiment
from tqdm import tqdm
# tqdm use for progress bar, or we called it tadaddum

class Command(BaseCommand):
    help = 'Update cleaned_text and sentiment for existing conversatios'

    # here we create method for argument out of handle method
    # so here we have two parser as an option
    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of messages to process at once'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-process all messages (even if already processed)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        force = options['force']

        if force:
            conversations = Conversation.objects.all()
            self.stdout.write("🔄 Force mode: Re-processing ALL messages...")
        else:
            conversations = Conversation.objects.filter(
                sentiment__isnull=True
            )
            self.stdout.write("processing messages without cleaned_text ... ")
        
        total = conversations.count()

        if total == 0:
            self.stdout.write(self.style.SUCCESS("✅ No messages need processing"))
            return
        
        self.stdout.write(f"📊 Found {total} messages to process\n")

        processed = 0
        updated = 0

        # process in batches
        for i in range(0, total, batch_size):
            batch = conversations[i:i+batch_size]

            for conv in tqdm(batch, desc="Processing messages"):
                # clean text process
                cleaned = clean_text(conv.message)
                conv.cleaned_text = cleaned

                # analyze sentiment
                sentiment = analyze_sentiment(cleaned) if conv.client else None
                conv.sentiment = sentiment

                conv.save()
                updated += 1
                processed += 1

            self.stdout.write(f"    Progress: {processed}/{total}")

        self.stdout.write(self.style.SUCCESS(f"\n✅ Completed! Updated {updated} messages"))
