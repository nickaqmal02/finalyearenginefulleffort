from django.core.management.base import BaseCommand
from chat_analyzer.models import Topic

class Command(BaseCommand):
    help = "Seed the 12 predefined therapy topics into the database"

    DEFINED_TOPICS = [
        {
            "name": "Speech & Communication Development",
            "description": "Languange development, speech milestones, communication patterns",
            "keywords": ["bercakap", "sebut", "perkataan", "ayat", "komunikasi", "interaksi"],
        },
        {
            "name": "Eating Habits & Food Acceptance",
            "description": "Feeding behavior, food preferences, apetite, mealtime challenges",
            "keywords": ["makan", "nasi", "bubur", "selera", "daging", "sayur", "minum", "suap", "lauk"],
        },
        {
            "name": "Tantrum & Behavior Management",
            "description": "Behavioral outbursts, emotional regulation, disciplinary challenges",
            "keywords": ["tantrum", "mengamuk", "merajuk", "menangis", "marah", "melawan", "sepak", "baling", "jerit", "ganas", "kurang tantrum"],
        },
        {
            "name": "Sleep Patterns",
            "description": "Sleep quality, bedtime routines, night waking, rest issues",
            "keywords": ["nyenyak","tidur","tido", "malam", "lena", "terjaga", "buaian", "rehat", "bangun"],
        },
        {
            "name": "Social Interaction",
            "description": "Peer relationships, play skills, social engangement",
            "keywords": ["main", "kawan", "gaul", "kongsi", "rakan", "sosial"],
        },
        {
            "name": "School & Academic Progress",
            "description": "School Performance, learning, focus, academic milestones",
            "keywords": ["school","sekolah", "cikgu", "fokus", "belajar", "baca", "tulis"],
        },
        {
            "name": "Physical Development",
            "description": "Motor skills, movemoment milestones, physical coordination",
            "keywords": ["aktif","gerak", "motor", "jalan", "lompat", "pegang", "pijak", "merangkak"],
        },
        {
            "name": "Therapy Progress",
            "description": "Treatment outcomes, improvements, development phase",
            "keywords": ["ubah", "terapi", "maju", "perubahan", "proses"],
        },
        {
            "name": "Parental Emotions",
            "description": "Parent feelings, stress, hopes, emotional wellbeing",
            "keywords": ["suka","risau", "sedih", "kecewa", "stress", "penat", "gembira", "syukur"],
        },
        {
            "name": "Family Environment",
            "description": "Home Situation, family dynamics, household context",
            "keywords": ["rumah", "keluarga", "ibu", "ayah", "kakak", "abang"],
        },
        {
            "name": "Sensory Integration",
            "description": "Sensory processing, stimuli response, attention regulation",
            "keywords": ["sensory", "rangsangan", "fokus", "perhatian", "integrasi"],
        },
        {
            "name": "Treatment Methods",
            "description": "Therapy techniques, session approaches, intervention methods",
            "keywords": ["balutan","sapu", "balut", "urut", "rawatan", "sesi", "latih", "teknik", "kaedah", "session"],
        },
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🌱 Seeding the therapy topics... "))

        created_count = 0
        updated_count = 0

        for topic_data in self.DEFINED_TOPICS:
            topic_obj, created = Topic.objects.update_or_create(
                name=topic_data["name"],
                defaults={
                    "description": topic_data["description"],
                    "keywords": topic_data["keywords"],
                    "is_active": True,
                },
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f"   ✅ Created: {topic_obj.name}")
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f"   🧻 Updated: {topic_obj.name}")
                )
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n Done {created_count} created, {updated_count} updated"
            )
        )


