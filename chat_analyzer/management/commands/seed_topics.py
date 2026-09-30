from django.core.management.base import BaseCommand
from chat_analyzer.models import Topic

class Command(BaseCommand):
    help = "Seed the 12 predefined therapy topics into the database"

    DEFINED_TOPICS = [
        {
            "name": "Progress and Sessions",
            "description": "Overall therapy progress and session-related updates",
            "keywords": ["perkembangan", "sesi", "mula", "anak", "perubahan", "therapy", "terapi", "rawatan", "improvement", "maju", "proses", "konsisten", "fasa"],
        },
        {
            "name": "Behaviour and Transitions",
            "description": "Behaviour changes, tantrums, eating habits, sensory responses",
            "keywords": ["anak", "makan", "perubahan", "mula", "nak", "tantrum", "mengamuk", "menangis", "marah", "lari", "perangai", "meraung", "mengadu", "kawan"],
        },
        {
            "name": "Sleep and Routine",
            "description": "Sleep patterns, bedtime, night routine, wrapping therapy",
            "keywords": ["tidur", "malam", "lena", "nyenyak", "tidur", "balut", "kepala", "rehat", "bangun", "mata", "terjaga", "buai"],
        },
        {
            "name": "Speech and Emotional Feedback",
            "description": "Speech development and emotional responses from parents/doctors",
            "keywords": ["perkembangan", "positif", "nampak", "sikit", "doktor", "cakap", "bercakap", "sebut", "perkataan", "komunikasi", "syukur", "gembira", "happy", "respond"],
        },
        {
            "name": "School and Play Interaction",
            "description": "School activities, teacher feedback, play, treatment sessions",
            "keywords": ["cikgu", "minggu", "sekolah", "tantrum", "rawatan", "main", "bermain", "play", "kawan", "rakan", "belajar", "tulis", "baca", "kelas"],
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


