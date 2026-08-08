from django.core.management.base import BaseCommand
from chat_analyzer.models import Admin, Client

class Command(BaseCommand):
    help = 'get all clients from specific admin'

    def handle(self, *args, **options):

        try:
            admin = Admin.objects.get(username='admin')
            clients = Client.objects.filter(registered_by=admin)
            
            client_count = clients.count()
            
            if client_count == 0:
                self.stdout.write(self.style.WARNING(f'No clients found for username admin: { admin.username }'))
                return
            
            # Header
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS(f"  CLIENTS REPORT FOR ADMIN: { admin.username }"))
            self.stdout.write("=" * 60)
            
            # Summary
            self.stdout.write(f"  Total Clients Found: {self.style.SUCCESS(str(client_count))}")
            self.stdout.write("-" * 60)
            
            # Client details with separators
            for index, client in enumerate(clients, start=1):
                self.stdout.write(f"\n  Client #{index}")
                self.stdout.write(f"  ├── Username    : {client.username}")
                # self.stdout.write(f"  ├── Phone Number: {client.phone_number}")

                # display all contacts that associate with 
                contacts = client.contacts.all()
                if contacts.exists():
                    self.stdout.write(f"   |--- Contacts: ")
                    for i, contact in enumerate(contacts):
                        prefix = "  |. |-- " if i == contacts.count() - 1 else "  |   |-- "
                        self.stdout.write(f"  │   {prefix} {contact.get_contact_type_display()}: {contact.name} ({contact.phone_number}){' ⭐' if contact.is_primary else ''}")
                else:
                    self.stdout.write(f"  ├── Contacts: None")
                if hasattr(client, 'email'):  # If email field exists
                    self.stdout.write(f"  └── Email       : {client.email}")
                else:
                    self.stdout.write(f"  └── {'-' * 30}")
            
            # Footer
            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS(f"✓ Report generated successfully"))
            self.stdout.write("=" * 60 + "\n")

        except Admin.DoesNotExist:
            self.stdout.write(self.style.ERROR('✗ Admin does not exist'))
            return
        