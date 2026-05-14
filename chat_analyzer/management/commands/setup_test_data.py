from django.core.management.base import BaseCommand
from chat_analyzer.models import Admin, Therapist, Client

class Command(BaseCommand):
    help = 'Setup test data for development'

    def handle(self, *args, **options):
        self.stdout.write("=" * 10)
        self.stdout.write(" SETUP TEST DATA ")
        self.stdout.write("=" * 10)

        # create admin
        admin, created = Admin.objects.get_or_create(
            username='admin',
            defaults={
                'name': 'System Admin',
                'phone_number': '0123456789'

            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS(" Admin Created"))

        else:
            self.stdout.write("Admin already exists")

        # Create Therapist
        therapist, created = Therapist.objects.get_or_create(
            username= 'therapist1',
            defaults={
                'name': 'Sarah Abdullah',
                'phone_number': '0179716757',
                'specialization': 'Autism Therapy',
                'registered_by': admin
            }
        )

        if created:
            therapist.set_password('therapist123')
            therapist.save()
            self.stdout.write(" Therapist Created ")
        else:
            self.stdout.write("therapist already exists")

        #create client
        client, created = Client.objects.get_or_create(
            phone_number = '+60 16-878 7787',
            defaults={
                'parent_name': 'Ahmad Abdullah',
                'child_name': 'Alia',
                'registered_by': admin,
                'assigned_therapist': therapist

            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("client created"))
        else:
            self.stdout.write("client already exists")


        #

        self.stdout.write("=" * 10)
        self.stdout.write(self.style.SUCCESS("setup complete"))
        self.stdout.write(f"    Admin = admin/ admin123")
        self.stdout.write(f"    Therapist: therapist1/ therapist123")
        self.stdout.write("=" * 10)
