from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'show the admin registeration invite code'

    def handle(self, *args, **options):
        self.stdout.write("=" * 50)
        self.stdout.write("📋 ADMIN INVITE CODE")
        self.stdout.write("=" * 50)
        self.stdout.write(f"Invite Code: {settings.ADMIN_INVITE_CODE}")
        self.stdout.write("=" * 50)
        self.stdout.write("Share this code ONLY with trusted people!")
        self.stdout.write("=" * 50)

