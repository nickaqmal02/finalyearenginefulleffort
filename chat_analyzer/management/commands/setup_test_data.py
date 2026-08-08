import random
from django.core.management.base import BaseCommand
from chat_analyzer.models import Admin, Therapist, Client, ClientContact

class Command(BaseCommand):
    help = 'Setup test data with EXACT and RANDOM clients'

    def handle(self, *args, **options):
        # Get admin
        admin, _ = Admin.objects.get_or_create(
            username='admin',
            defaults={'name': 'System Admin', 'phone_number': '0123456789'}
        )
        admin.set_password('admin123')
        admin.save()
        
        # Get or create therapist
        therapist, _ = Therapist.objects.get_or_create(
            username='therapist1',
            defaults={
                'name': 'Test Therapist',
                'phone_number': '0191234567',
                'specialization': 'General Therapy',
                'registered_by': admin,
                'is_active': True
            }
        )
        if therapist._state.adding:
            therapist.set_password('therapist123')
            therapist.save()
        
        # ========== CREATE CLIENTS WITH CONTACTS ==========
        self.stdout.write("\n📌 Creating clients with contacts...")
        
        test_clients = [
            ('Ahmad Abdullah', 'Alia', ['+60 16-935 4580', '+60 12-345 6789']),
            ('Sarah Tan', 'Adam', ['+60 12-345 6789']),
            ('Raj Kumar', 'Arjun', ['+60 11-222 3333']),
        ]
        
        for parent, child, phones in test_clients:
            client, created = Client.objects.get_or_create(
                parent_name=parent,
                child_name=child,
                defaults={
                    'registered_by': admin,
                    'assigned_therapist': therapist,
                    'status': 'active'
                }
            )
            
            if created:
                # Add contacts
                for i, phone in enumerate(phones):
                    ClientContact.objects.create(
                        client=client,
                        contact_type='father' if i == 0 else 'mother',
                        name=parent,
                        phone_number=phone,
                        is_primary=(i == 0)
                    )
                self.stdout.write(f"  ✅ Created: {parent} - {len(phones)} phone(s)")
            else:
                self.stdout.write(f"  📌 Already exists: {parent}")
        
        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(self.style.SUCCESS(f"✅ Total Clients: {Client.objects.count()}"))
        self.stdout.write(self.style.SUCCESS(f"✅ Total Contacts: {ClientContact.objects.count()}"))
        self.stdout.write("=" * 50)