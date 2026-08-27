import logging

from django.core.management.base import BaseCommand
from django.db import transaction
# we will use transaction function from built in django db 
#
from chat_analyzer.models import Conversation
from chat_analyzer.services.text_cleaner import get_cleaner

# creating the logger object first
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Re clean all Conversations with the current text cleaner ( no re upload ) '

    def add_argument(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='show what would be cleaned without saving',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        cleaner = get_cleaner()

        conversations = Conversation.objects.all()
        total = conversations.count()

        self.stdout.write(self.style.SUCCESS(f'\n ....... RECLEANING PROCESS IN PROGRESS '))
        self.stdout.write('=' * 60)

        cleaned = 0

        with transaction.atomic():
            for conv in conversations:
                new_sentiment = cleaner.clean_for_sentiment(conv.message)
                new_topic = cleaner.clean_for_topic_modeling(conv.message)
                
                if dry_run:
                    self.stdout.write(f'\n [{conv.id}] {conv.message[:50]}..... ')
                    self.stdout.write(f'    topic: {new_topic}')
                    continue
                
                conv.cleaned_text = new_sentiment
                conv.cleaned_text_topic = new_topic
                conv.is_cleaned_sentiment = True
                conv.is_cleaned_topic = True
                conv.save()
                cleaned += 1

                if cleaned % 50 == 0:
                    self.stdout.write(f' cleaned {cleaned}/{total}...')

        if dry_run:
            self.stdout.write(self.style.WARNING('\n DRY RUN - NOTHING SAVED'))
        else:
            self.stdout.write(self.style.SUCCESS(f' Re cleaned {cleaned} conversations'))
        self.stdout.write('=' * 60)


