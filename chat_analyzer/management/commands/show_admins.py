from django.core.management.base import BaseCommand
from chat_analyzer.models import Admin

class Command(BaseCommand):
    help = 'show all admin users'

    def handle(self, *args, **options):
        admins = Admin.objects.all()

        if not admins:
            self.stdout.write(self.style.WARNING("No admin users found. "))
            return
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS(f"📊 TOTAL ADMINS: {admins.count()}"))
        self.stdout.write("=" * 60)

        for admin in admins:
            self.stdout.write(f"\n Admin ID: {admin.id}")
            self.stdout.write(f"    Username: {admin.username}")
            self.stdout.write(f"    Name: {admin.name}")
            self.stdout.write(f"    Phone: {admin.phone_number}")
            self.stdout.write(f"    Created: {admin.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            self.stdout.write("-" * 40)
        
        self.stdout.write("=" * 60)

        
