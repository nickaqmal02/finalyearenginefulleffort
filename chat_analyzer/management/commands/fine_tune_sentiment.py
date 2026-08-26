from django.core.management.base import BaseCommand
from chat_analyzer.services.fine_tune_sentiment import fine_tune_sentiment_model

class Command(BaseCommand):
    help = 'Fine-tune the sentiment model on labeled data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n Fine-tuning sentiment model \n'))
        self.stdout.write('=' * 60)

        try:
            fine_tune_sentiment_model()
            self.stdout.write(self.style.SUCCESS('\n Fine tuning complete'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n ❌ Error: {e}'))
            import traceback
            traceback.print_exc()



