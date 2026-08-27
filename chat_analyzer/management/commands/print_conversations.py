from django.core.management.base import BaseCommand
from chat_analyzer.models import Conversation

class Command(BaseCommand):
    help = 'for printing those conversation for testing under development'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Max rows to print'
        )
        parser.add_argument(
            '--topic',
            action='store_true',
            help='also show cleaned_topic'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        show_topic = options.get('topic', False)

        convs = Conversation.objects.all()[:limit]
        total = Conversation.objects.count()
        self.stdout.write(self.style.SUCCESS(f'showing this {min(limit, total)} of {total}\n'))
        self.stdout.write('=' * 70)

        for i, c in enumerate(convs, 1):
            self.stdout.write(f'\n [{i}] | id={c.id}) | client={c.client_id} | sender = {c.sender_id}')
            self.stdout.write(f'    original : {c.message}')
            self.stdout.write(f'    cleaned_sentiment: {c.cleaned_text} ')
            self.stdout.write(f'    cleaned_topic: {c.cleaned_text_topic} ')

            if show_topic:
                self.stdout.write(f' topic: ')

        self.stdout.write('=' * 70)


