from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'simple hello world'

    def handle(self, *args, **options):
        self.stdout.write("=" * 90)
        self.stdout.write(self.style.SUCCESS("hello world"))
        self.stdout.write(f"hai ainur mardiah I love you so much till first day I met you, most ardently darlings <33")
        self.stdout.write(self.style.WARNING("hai ainur mardiah I love you so much till first day I met you, most ardently darlings <33"))
        self.stdout.write(f"hai ainur mardiah I love you so much till first day I met you, most ardently darlings <33")