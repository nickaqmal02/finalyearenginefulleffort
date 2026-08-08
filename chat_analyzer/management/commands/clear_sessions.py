from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Clear all sessions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-user',
            type=str,
            help='Username to keep session for',
        )

    def handle(self, *args, **options):
        sessions = Session.objects.all()
        count = sessions.count()
        
        if options.get('keep_user'):
            try:
                user = User.objects.get(username=options['keep_user'])
                sessions = sessions.exclude(session_key=user.session.session_key)
            except (User.DoesNotExist, AttributeError):
                pass
        
        sessions.delete()
        self.stdout.write(
            self.style.SUCCESS(f'Successfully cleared {count} session(s)')
        )
