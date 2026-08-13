# chat_analyzer/management/commands/create_test_users.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from chat_analyzer.models import ClientContact
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users for development (Admins, Therapists, Doctors, Clients)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clients',
            type=int,
            default=10,
            help='Number of clients to create (default: 10)'
        )
        parser.add_argument(
            '--therapists',
            type=int,
            default=4,
            help='Number of therapists to create (default: 4)'
        )
        parser.add_argument(
            '--doctors',
            type=int,
            default=2,
            help='Number of doctors to create (default: 2)'
        )
        parser.add_argument(
            '--admins',
            type=int,
            default=2,
            help='Number of admins to create (default: 2)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if users already exist'
        )

    def handle(self, *args, **options):
        num_clients = options['clients']
        num_therapists = options['therapists']
        num_doctors = options['doctors']
        num_admins = options['admins']
        force = options['force']

        self.stdout.write(self.style.SUCCESS('\n👥 CREATING TEST USERS\n'))
        self.stdout.write('=' * 60)

        # Create users
        admins = self.create_admins(num_admins, force)
        therapists = self.create_therapists(num_therapists, force)
        doctors = self.create_doctors(num_doctors, force)
        clients = self.create_clients(num_clients, therapists, force)

        # Show summary
        self.show_summary(admins, therapists, doctors, clients)

    # ============================================
    # CREATE ADMINS
    # ============================================
    def create_admins(self, count, force):
        """Create admin users."""
        self.stdout.write('\n👤 Creating Admins...')
        admins = []

        admin_data = [
            ('admin1', 'John', 'Admin', 'john.admin@sentiri.com'),
            ('admin2', 'Sarah', 'Admin', 'sarah.admin@sentiri.com'),
        ]

        for i in range(count):
            if i < len(admin_data):
                username, first, last, email = admin_data[i]
            else:
                username = f'admin{i+1}'
                first = f'Admin{i+1}'
                last = 'User'
                email = f'{username}@sentiri.com'

            # ✅ FIX: Check if user exists first
            user = User.objects.filter(username=username).first()

            if user:
                if force:
                    user.first_name = first
                    user.last_name = last
                    user.email = email
                    user.role = 'admin'
                    user.is_staff = True
                    user.is_superuser = True if i == 0 else False
                    user.is_active = True
                    user.save()
                    self.stdout.write(self.style.WARNING(f'  🔄 Updated Admin: {username}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⏭️ Admin already exists: {username}'))
                admins.append(user)
            else:
                # ✅ Create user properly with password
                user = User.objects.create_user(
                    username=username,
                    password='admin123',
                    email=email,
                    first_name=first,
                    last_name=last,
                )
                user.role = 'admin'
                user.is_staff = True
                user.is_superuser = True if i == 0 else False
                user.is_active = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created Admin: {username}'))
                admins.append(user)

        return admins

    # ============================================
    # CREATE THERAPISTS
    # ============================================
    def create_therapists(self, count, force):
        """Create therapist users."""
        self.stdout.write('\n👤 Creating Therapists...')
        therapists = []

        therapist_data = [
            ('therapist1', 'Aina', 'Razak', 'aina@sentiri.com', 'Clinical Psychology'),
            ('therapist2', 'Daniel', 'Tan', 'daniel@sentiri.com', 'Child Psychology'),
            ('therapist3', 'Farah', 'Ismail', 'farah@sentiri.com', 'Behavioral Therapy'),
            ('therapist4', 'Kumar', 'Raj', 'kumar@sentiri.com', 'Speech Therapy'),
        ]

        for i in range(count):
            if i < len(therapist_data):
                username, first, last, email, spec = therapist_data[i]
            else:
                username = f'therapist{i+1}'
                first = f'Therapist{i+1}'
                last = 'User'
                email = f'{username}@sentiri.com'
                spec = 'General Therapy'

            user = User.objects.filter(username=username).first()

            if user:
                if force:
                    user.first_name = first
                    user.last_name = last
                    user.email = email
                    user.phone = f"+6012{random.randint(10000000, 99999999)}"
                    user.specialization = spec
                    user.is_active = True
                    user.save()
                    self.stdout.write(self.style.WARNING(f'  🔄 Updated Therapist: {username}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⏭️ Therapist already exists: {username}'))
                therapists.append(user)
            else:
                user = User.objects.create_user(
                    username=username,
                    password='therapist123',
                    email=email,
                    first_name=first,
                    last_name=last,
                )
                user.role = 'therapist'
                user.phone = f"+6012{random.randint(10000000, 99999999)}"
                user.license_number = f"LIC-{username.upper()}"
                user.license_state = 'Selangor'
                user.years_of_experience = random.randint(2, 8)
                user.hire_date = '2024-01-01'
                user.specialization = spec
                user.is_active = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created Therapist: {username}'))
                therapists.append(user)

        return therapists

    # ============================================
    # CREATE DOCTORS
    # ============================================
    def create_doctors(self, count, force):
        """Create doctor users."""
        self.stdout.write('\n👤 Creating Doctors...')
        doctors = []

        doctor_data = [
            ('doctor1', 'Dr. Ahmad', 'Hassan', 'ahmad@sentiri.com', 'Child Psychiatry'),
            ('doctor2', 'Dr. Lisa', 'Wong', 'lisa@sentiri.com', 'Developmental Pediatrics'),
        ]

        for i in range(count):
            if i < len(doctor_data):
                username, first, last, email, spec = doctor_data[i]
            else:
                username = f'doctor{i+1}'
                first = f'Doctor{i+1}'
                last = 'User'
                email = f'{username}@sentiri.com'
                spec = 'General Psychiatry'

            user = User.objects.filter(username=username).first()

            if user:
                if force:
                    user.first_name = first
                    user.last_name = last
                    user.email = email
                    user.specialization = spec
                    user.is_active = True
                    user.save()
                    self.stdout.write(self.style.WARNING(f'  🔄 Updated Doctor: {username}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⏭️ Doctor already exists: {username}'))
                doctors.append(user)
            else:
                user = User.objects.create_user(
                    username=username,
                    password='doctor123',
                    email=email,
                    first_name=first,
                    last_name=last,
                )
                user.role = 'doctor'
                user.phone = f"+6013{random.randint(10000000, 99999999)}"
                user.license_number = f"MD-{username.upper()}"
                user.license_state = 'Selangor'
                user.years_of_experience = random.randint(8, 20)
                user.hire_date = '2018-01-01'
                user.specialization = spec
                user.is_active = True
                user.save()
                self.stdout.write(self.style.SUCCESS(f'  ✅ Created Doctor: {username}'))
                doctors.append(user)

        return doctors

    # ============================================
    # CREATE CLIENTS
    # ============================================
    def create_clients(self, count, therapists, force):
        """Create client users with contacts."""
        self.stdout.write('\n👤 Creating Clients...')
        clients = []

        if not therapists:
            self.stdout.write(self.style.ERROR('  ❌ No therapists available! Please create therapists first.'))
            return []

        client_data = [
            ('client1', 'Ahmad Fauzi', 'Arif', '+60123456789', 'father'),
            ('client2', 'Siti Aishah', 'Maya', '+60123456790', 'mother'),
            ('client3', 'Ravi Kumar', 'Anita', '+60123456791', 'father'),
            ('client4', 'Lim Mei Ling', 'Jun', '+60123456792', 'mother'),
            ('client5', 'Sarah Tan', 'Ethan', '+60123456793', 'mother'),
            ('client6', 'Mohd Azri', 'Haziq', '+60123456794', 'father'),
            ('client7', 'Nurul Huda', 'Dania', '+60123456795', 'mother'),
            ('client8', 'David Ng', 'Sam', '+60123456796', 'father'),
            ('client9', 'Fazura Ismail', 'Amira', '+60123456797', 'mother'),
            ('client10', 'Jeffrey Ong', 'Kate', '+60123456798', 'father'),
        ]

        admin1 = User.objects.filter(username='admin1').first()
        if not admin1:
            admin1 = User.objects.filter(role='admin').first()

        if not admin1:
            self.stdout.write(self.style.ERROR('  ❌ No admin found! Please create admins first.'))
            return []

        for i in range(min(count, len(client_data))):
            username, parent_name, child_name, phone, contact_type = client_data[i]
            therapist = therapists[i % len(therapists)]

            user = User.objects.filter(username=username).first()

            if user:
                if force:
                    user.first_name = parent_name
                    user.last_name = child_name
                    user.phone = phone
                    user.client_status = 'active'
                    user.registered_by = admin1
                    user.assigned_therapist = therapist
                    user.is_active = True
                    user.save()

                    contact, _ = ClientContact.objects.get_or_create(
                        client=user,
                        defaults={
                            'contact_type': contact_type,
                            'name': parent_name,
                            'phone_number': phone,
                            'is_primary': True,
                        }
                    )
                    self.stdout.write(self.style.WARNING(f'  🔄 Updated Client: {username}'))
                else:
                    self.stdout.write(self.style.WARNING(f'  ⏭️ Client already exists: {username}'))
                clients.append(user)
            else:
                user = User.objects.create_user(
                    username=username,
                    password='client123',
                    email=f'{username}@sentiri.com',
                    first_name=parent_name,
                    last_name=child_name,
                )
                user.role = 'client'
                user.phone = phone
                user.client_status = 'active'
                user.registered_by = admin1
                user.assigned_therapist = therapist
                user.is_active = True
                user.save()

                ClientContact.objects.create(
                    client=user,
                    contact_type=contact_type,
                    name=parent_name,
                    phone_number=phone,
                    is_primary=True,
                )

                self.stdout.write(self.style.SUCCESS(f'  ✅ Created Client: {username} ({child_name}) → {therapist.username}'))
                clients.append(user)

        return clients

    # ============================================
    # SHOW SUMMARY
    # ============================================
    def show_summary(self, admins, therapists, doctors, clients):
        """Show summary of created users."""
        self.stdout.write(self.style.SUCCESS('\n📊 CREATION SUMMARY\n'))
        self.stdout.write('=' * 60)

        self.stdout.write(f'\n👤 Admins: {len(admins)}')
        for admin in admins:
            self.stdout.write(f'  - {admin.username} ({admin.first_name} {admin.last_name})')

        self.stdout.write(f'\n👤 Therapists: {len(therapists)}')
        for therapist in therapists:
            self.stdout.write(f'  - {therapist.username} ({therapist.first_name} {therapist.last_name})')

        self.stdout.write(f'\n👤 Doctors: {len(doctors)}')
        for doctor in doctors:
            self.stdout.write(f'  - {doctor.username} ({doctor.first_name} {doctor.last_name})')

        self.stdout.write(f'\n👤 Clients: {len(clients)}')
        for client in clients:
            therapist = client.assigned_therapist
            therapist_name = therapist.username if therapist else 'Unassigned'
            self.stdout.write(f'  - {client.username} ({client.last_name}) → {therapist_name}')

        self.stdout.write(self.style.SUCCESS('\n✅ All users created successfully!\n'))
        self.stdout.write('=' * 60)
        self.stdout.write('\n🔑 Default Passwords:')
        self.stdout.write('  - Admins: admin123')
        self.stdout.write('  - Therapists: therapist123')
        self.stdout.write('  - Doctors: doctor123')
        self.stdout.write('  - Clients: client123')
        self.stdout.write('\n' + '=' * 60)
