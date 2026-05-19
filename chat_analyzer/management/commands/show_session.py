from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session

class Command(BaseCommand):
    help = 'Show current active sessions'

    def handle(self, *args, **options):
        sessions = Session.objects.all()

        if not sessions:
            self.stdout.write("No active sessions")
            return
        
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("ACTIVE SESSIONS")
        self.stdout.write("=" * 50)

        for session in sessions:
            data = session.get_decoded()
            self.stdout.write(f"User: {data.get('user_name', 'Unknown')}")
            self.stdout.write(f"Role: {data.get('user_role', 'Unknown')}")
            self.stdout.write(f"User ID: {data.get('user_id', 'Unknown')}")
            self.stdout.write("-" * 30)

        self.stdout.write(f"Total: {sessions.count()} active session(s)")
