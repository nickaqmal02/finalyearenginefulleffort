# like always most professional using management command
from django.core.management.base import BaseCommand
from chat_analyzer.models import Admin, Therapist

class Command(BaseCommand):
    help = "create 5 test therapists"

    def handle(self, *args, **options):
        #admin = Admin.objects.first() # this are the reason why it links to first created admins
        admin = Admin.objects.get(username='admin') # this line will ensure that it linked to which admin account that we want to use
        if not admin:
            self.stdout.write(self.style.ERROR('No admin found. Create admin first. '))

            return
    
        therapists_data = [
            {'username': 'therapist_sarah', 'name': 'Sarah Abdullah', 'phone': '0191234567', 'specialization': 'Autism Behavioral Therapy'},
            {'username': 'therapist_ahmad', 'name': 'Ahmad Fauzi', 'phone': '0192345678', 'specialization': 'Speech Therapy'},
            {'username': 'therapist_priya', 'name': 'Priya Raju', 'phone': '0193456789', 'specialization': 'Occupational Therapy'},
            {'username': 'therapist_lisa', 'name': 'Lisa Lim', 'phone': '0194567890', 'specialization': 'Child Psychology'},
            {'username': 'therapist_raj', 'name': 'Raj Kumar', 'phone': '0195678901', 'specialization': 'ABA Therapy'},
        ]

        created_count = 0
        for data in therapists_data:
            therapist, created = Therapist.objects.get_or_create(
                username=data['username'],
                defaults={
                    'name': data['name'],
                    'phone_number': data['phone'],
                    'specialization': data['specialization'],
                    'registered_by': admin,
                    'is_active': True
                }
            )
            if created:
                therapist.set_password('therapist123')
                therapist.save()
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"✅ Created: {therapist.name}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"📌 Already exists: {therapist.name}"))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Created {created_count} new therapists"))   
        self.stdout.write(f"📊 Total therapists: {Therapist.objects.count()}")
        self.stdout.write("🔑 Password: therapist123")
