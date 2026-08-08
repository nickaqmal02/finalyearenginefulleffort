from django.core.management.base import BaseCommand
from chat_analyzer.models import Admin, Therapist, Client, ClientContact

class Command(BaseCommand):
    help = 'Setup clean test data with proper contacts'

    def handle(self, *args, **options):
        # get or create admin
        admin, _ = Admin.objects.get_or_create(
            username='admin',
            defaults={'name': 'System Admin', 'phone_number': '0123456789'}
        )
        admin.set_password('admin123')
        admin.save()
        self.stdout.write("✅ Admin Ready ")

        # get or create therapist
        therapist, _ = Therapist.objects.get_or_create(
            username='therapist1',
            defaults={
                'name': 'Sarah Abdullah',
                'phone_number': '0192234454',
                'specialization': 'Autism Therapy',
                'registered_by': admin,
                'is_active': True
            }
        )
        if therapist._state.adding:
            therapist.set_password('therapist123')
            therapist.save()
        self.stdout.write("✅ Therapist ready")

        # Client 1: Ahmad Abdullah (Father primary, Mother secondary)
        client1 = Client.objects.create(
            username = 'ahmad_abdullah',
            parent_name='Ahmad Abdullah',
            child_name='Alia',
            registered_by=admin,
            assigned_therapist=therapist,
            status='active'
        )
        ClientContact.objects.create(
            client=client1,
            contact_type='father',
            name='Ahmad Abdullah',
            phone_number='+60 16-935 4580',
            is_primary=True
        )
        ClientContact.objects.create(
            client=client1,
            contact_type='mother',
            name='Siti Nur',
            phone_number='+60 12-345 6789',
            is_primary=True
        )
        ClientContact.objects.create(
            client=client1,
            contact_type='guardian',
            name='Makcik Kiah',
            phone_number='+60 19-888 7777',
            is_primary=True
        )
        self.stdout.write(self.style.SUCCESS(f"✅ Client: {client1.parent_name} - 3 contacts"))


        # client 2: Sarah Tan (Mother primary only)
        client2 = Client.objects.create(
            username = 'sarah_tan',
            parent_name = 'Sarah Tan',
            child_name='Adam',
            registered_by = admin,
            assigned_therapist=therapist,
            status='active'
        )
        ClientContact.objects.create(
            client=client2,
            contact_type='mother',
            name='Sarah Tan',
            phone_number='+60 11-222 3333',
            is_primary=True
        )
        self.stdout.write(self.style.SUCCESS(f"✅ Client: {client2.parent_name} - 1 contact"))

        # Client 3: Raj Kumar (Father primary, Grandmother secondary)
        client3 = Client.objects.create(
            username='raj_kumar',
            parent_name='Raj Kumar',
            child_name='Arjun',
            registered_by=admin,
            assigned_therapist=therapist,
            status='active'
        )
        ClientContact.objects.create(
            client=client3,
            contact_type='father',
            name='Raj Kumar',
            phone_number='+60 17-666 5555',
            is_primary=True
        )
        ClientContact.objects.create(
            client=client3,
            contact_type='guardian',
            name="Raj's Mother",
            phone_number= '+60 18-44 9999',
            is_primary=False
        )
        self.stdout.write(self.style.SUCCESS(f"✅ Client: {client3.parent_name} - 2 contacts"))

        # summary 
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(f"✅ CLEAN DATA SETUP COMPLETE"))

        self.stdout.write(f"    Clients: {Client.objects.count()}")
        self.stdout.write(f"    Contacts: {ClientContact.objects.count()}")
        self.stdout.write("=" * 50)

