from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'simple hello world'

    def handle(self, *args, **options):
        self.stdout.write("=" * 20)
        self.stdout.write(self.style.SUCCESS("hello world"))