import random
from django.core.management.base import BaseCommand
from chat_analyzer.models import Admin, Therapist, Client

class Command(BaseCommand):
    help = 'Setup test data with EXACT and RANDOM clients'

    def handle(self, *args, **options):
        # get admin
        admin, _ = Admin.objects.get_or_create(
            username='admin',
            defaults={'name': 'System Admin', 'phone_number': '0123456789'}
        )
        admin.set_password('admin123')
        admin.save()

        # ====== EXACT DATA FOR PREDICTABLE TESTING LAH ========
        self.stdout.write(self.style.WARNING("\n Creating EXACT test clients... "))

        exact_clients = [
            # these will match by phone number
            {'parent_name': 'Ahmad Abdullah', 'child_name': 'Alia', 'phone': '+60 16-935 4580', 'username': 'ahmad_abdullah'},
            {'parent_name': 'Sarah Tan', 'child_name': 'Adam', 'phone': '+60 12-345 6789', 'username': 'sarah_tan'},
            {'parent_name': 'Raj Kumar', 'child_name': 'Arjun', 'phone': '+60 11-222 3333', 'username': 'raj_kumar'},

            # these will match by username ( if whatsapp shows name )
            {'parent_name': 'Mei Wong', 'child_name': 'Little Mei', 'phone': '+60 19-888 7777', 'username': 'Mei Wong'},
            {'parent_name': 'David Smith', 'child_name': 'Baby David', 'phone': '+60 17-666 5555', 'username': 'David Smith'},

        ]

        for client_data in exact_clients:
            client, created = Client.objects.get_or_create(
                phone_number=client_data['phone'],
                defaults={
                    'username': client_data['username'],
                    'parent_name': client_data['parent_name'],
                    'child_name': client_data['child_name'],
                    'registered_by': admin,
                    'status': 'active',
                }
            )
            if created:
                self.stdout.write(f"✅ Exact: {client.parent_name} - {client.phone_number}")

        # ================= RANDOM DATA (FOR ROBUSTNESS TESTING) ==================
        self.stdout.write(self.style.WARNING("\n🎲 Creating RANDOM test clients..."))

        first_names = ['Ahmad', 'Sarah', 'Raj', 'Mei', 'David', 'Lisa', 'Mohamed', 'Priya', 'John', 'Siti']
        last_names = ['Abdullah', 'Tan', 'Kumar', 'Wong', 'Smith', 'Lim', 'Chong', 'Lee', 'Ng', 'Raj']
        child_names = ['Adam', 'Alia', 'Arjun', 'Sarah', 'David', 'Lisa', 'Aisyah', 'Ahmad', 'Mei', 'Raj']
        phone_prefixes = ['+60 16', '+60 12', '+60 11', '+60 19', '+60 17', '+60 18']

        for i in range(15): # 15 random clients
            phone = f"{random.choice(phone_prefixes)} {random.randint(1000000, 9999999)}"
            parent = f"{random.choice(first_names)} {random.choice(last_names)}"

            client, created = Client.objects.get_or_create(
                phone_number=phone,
                defaults={
                    'username': f"random_{i+1}",
                    'parent_name': parent,
                    'child_name': random.choice(child_names),
                    'registered_by': admin,
                    'status': random.choice(['active', 'active', 'active', 'inactive'])

                }
            )
            if created:
                self.stdout.write(f" 🎲 Random: {parent} - {phone} ")

        # summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(f"✅ Total Clients: {Client.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"     Exact: {len(exact_clients)}"))
        self.stdout.write(self.style.SUCCESS(f"     Random: 15"))
        self.stdout.write("=" * 50)
        
