from django.core.management.base import BaseCommand
from chat_analyzer.models import Client

class Command(BaseCommand):
    help = 'Export clients in CSV format'

    def handle(self, *args, **options):
        clients = Client.objects.all()
        
        # CSV Header
        self.stdout.write("ID,Parent Name,Child Name,Primary Phone,All Phones,Status,Created At")
        
        for client in clients:
            # Get primary phone
            primary_contact = client.get_primary_contact()
            primary_phone = primary_contact.phone_number if primary_contact else ""
            
            # Get all phones
            all_phones = ", ".join(client.get_all_phones())
            
            self.stdout.write(
                f"{client.id},"
                f"{client.parent_name},"
                f"{client.child_name},"
                f"{primary_phone},"
                f"{all_phones},"
                f"{client.status},"
                f"{client.created_at.strftime('%Y-%m-%d')}"
            )