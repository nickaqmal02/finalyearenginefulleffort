from django.core.management.base import BaseCommand
from chat_analyzer.models import Admin, Client

class Command(BaseCommand):
    help = 'import client information in csv style'

    def handle(self, *args, **options):

        try:
            admin = Admin.objects.get(username='admin')
            clients = Client.objects.filter(
                registered_by=admin
                # why registered by not 'admin'
            )

            # csv style printing
            self.stdout.write(self.style.MIGRATE_HEADING("Username, Phone Number"))
            for client in clients:
                self.stdout.write(f"{client.username},{client.phone_number}")
        except Admin.DoesNotExist:
            self.stdout.write(self.style.MIGRATE_HEADING("admin does not found"))
            return
        # what does it mean by return here ?
        # noted that we SUCCESS, ERROR, WARNING, MIGRATE_HEADING: colour biru
