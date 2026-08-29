from django.core.management.base import BaseCommand
from chat_analyzer.models import MessageTopic, Topic

# defining the seed topics 
SEEDED_TOPICS = [
    "Speech & Communication Development",
    "Eating Habits & Food Acceptance",
    "Tantrum & Behavior Management",
    "Sleep Patterns",
    "Social Interaction",
    "School & Academic Progress",
    "Physical Development",
    "Therapy Progress",
    "Parental Emotions",
    "Family Environment",
    "Sensory Integration",
    "Treatment Methods",
]

class Command(BaseCommand):
    help = "Wipe Messagetopic rows and delete non-seeded topics. PREVIEW only by default"

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Actually delete"
        )

    def handle(self, *args, **options):
        mt_count = MessageTopic.objects.count()
        rogue = Topic.objects.exclude(name__in=SEEDED_TOPICS)

        self.stdout.write(f"MessageTopic rows to wipe: {mt_count}")
        self.stdout.write(f"Topics to delete ({rogue.count()}):")
        for t in rogue:
            self.stdout.write(f"    [{t.id}] {t.name}")

        missing = [n for n in SEEDED_TOPICS if not Topic.objects.filter(name=n).exists()]
        if missing:
            self.stdout.write(self.style.WARNING(f"Seeded topics missing (run seed_topics after): {missing}"))

        if not options["confirm"]:
            self.stdout.write(self.style.NOTICE("PREVIEW ONLY - NOTHING DELETED. RE-RUN WITH --confirm." ))
            return

        deleted_mt, _ = MessageTopic.objects.all().delete()
        deleted_top, _ = rogue.delete()
        self.stdout.write(self.style.SUCCESS(
            f"Deleted {deleted_mt} MessageTopic rows, {deleted_top} Topic rows."
                f"Seeded topics remaining: {Topic.objects.count()}"
        ))




