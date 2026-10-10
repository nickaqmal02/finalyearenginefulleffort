"""
Management command to seed MasterSpecifier with official DSM-5 specifiers.
Source: DSM-5, page 88 — Autism Spectrum Disorder (299.00 / F84.0)

Usage:
    python manage.py seed_specifiers          # adds missing specifiers
    python manage.py seed_specifiers --clear   # clears all, then seeds
"""
from django.core.management.base import BaseCommand
from chat_analyzer.models import MasterSpecifier

# Official DSM-5 specifiers for Autism Spectrum Disorder
# Source: DSM-5 page 88, "Specify if:" section
DSM5_SPECIFIERS = [
# Intellectual impairment (with/without)
{
    "specifier_name": "With accompanying intellectual impairment",
    "specifier_category": "Intellectual",
    "is_positive_specifier": True,
    "dsm_code": "DSM-5-ASD-01",
    "definition": "The client has below-average intellectual functioning (IQ below 70). They may struggle with reasoning, problem-solving, planning, and abstract thinking. Often co-occurs with difficulties in daily living skills.",
},
{
    "specifier_name": "Without accompanying intellectual impairment",
    "specifier_category": "Intellectual",
    "is_positive_specifier": False,
    "dsm_code": "DSM-5-ASD-01",
    "definition": "The client has average or above-average intellectual functioning. They can reason and learn normally, but still have social communication deficits. Many were previously diagnosed with Asperger's Disorder in DSM-IV.",
},
# Language impairment (with/without)
{
    "specifier_name": "With accompanying language impairment",
    "specifier_category": "Language",
    "is_positive_specifier": True,
    "dsm_code": "DSM-5-ASD-02",
    "definition": "The client has significant difficulty with structural language — grammar, vocabulary, and forming sentences. They may be nonverbal or have delayed speech development.",
},
{
    "specifier_name": "Without accompanying language impairment",
    "specifier_category": "Language",
    "is_positive_specifier": False,
    "dsm_code": "DSM-5-ASD-02",
    "definition": "The client's structural language (grammar, vocabulary, sentence structure) is intact. They can form sentences correctly, but may still struggle with the social and pragmatic use of language.",
},
# Medical/genetic/environmental
{
    "specifier_name": "Associated with a known medical or genetic condition",
    "specifier_category": "Medical",
    "is_positive_specifier": True,
    "dsm_code": "DSM-5-ASD-03",
    "definition": "The client has a specific genetic syndrome or medical condition linked with autism. Examples: Fragile X syndrome, Rett syndrome, tuberous sclerosis, or Down syndrome.",
},
{
    "specifier_name": "Associated with a known environmental factor",
    "specifier_category": "Environmental",
    "is_positive_specifier": True,
    "dsm_code": "DSM-5-ASD-03",
    "definition": "The client was exposed to an environmental factor known to increase autism risk. Examples: prenatal valproic acid exposure, congenital rubella, very low birth weight, or prenatal infection.",
},
# Neurodevelopmental/mental/behavioral
{
    "specifier_name": "Associated with another neurodevelopmental disorder",
    "specifier_category": "Neurodevelopmental",
    "is_positive_specifier": True,
    "dsm_code": "DSM-5-ASD-04",
    "definition": "The client has autism plus another neurodevelopmental condition. Examples: ADHD, developmental coordination disorder, or specific learning disorders like dyslexia.",
},
{
    "specifier_name": "Associated with another mental disorder",
    "specifier_category": "Mental",
    "is_positive_specifier": True,
    "dsm_code": "DSM-5-ASD-04",
    "definition": "The client has autism plus a mental health condition. Examples: anxiety disorder, depression, or obsessive-compulsive disorder (OCD).",
},
{
    "specifier_name": "Associated with another behavioral disorder",
    "specifier_category": "Behavioral",
    "is_positive_specifier": True,
    "dsm_code": "DSM-5-ASD-04",
    "definition": "The client has autism plus a behavioral condition. Examples: oppositional defiant disorder (ODD), conduct disorder, or disruptive behavior patterns.",
},
# Catatonia
{
    "specifier_name": "With catatonia",
    "specifier_category": "Behavioral",
    "is_positive_specifier": True,
    "dsm_code": "DSM-5-ASD-05",
    "definition": "The client shows catatonic symptoms — motor abnormalities like immobility, excessive movement, extreme negativism, mutism, posturing, or staring. This is a rare but serious condition requiring immediate medical attention.",
},
]


class Command(BaseCommand):
    help = 'Seed MasterSpecifier with official DSM-5 Autism Spectrum Disorder specifiers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear all existing specifiers before seeding (KEEPS existing — use carefully)',
        )

    def handle(self, *args, **options):
        clear = options.get('clear', False)

        if clear:
            deleted = MasterSpecifier.objects.all().delete()[0]
            self.stdout.write(self.style.WARNING(f'🗑️ Cleared {deleted} existing specifier(s)'))

        created_count = 0
        skipped_count = 0

        for spec_data in DSM5_SPECIFIERS:
            obj, created = MasterSpecifier.objects.update_or_create(
                specifier_name=spec_data["specifier_name"],
                defaults=spec_data,
            )
            if created:
                created_count += 1
                self.stdout.write(f'  ✅ Created: {spec_data["specifier_name"]}')
            else:
                skipped_count += 1
                self.stdout.write(f'  🔄 Updated: {spec_data["specifier_name"]}')

        total = MasterSpecifier.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\n✅ Done! Created {created_count} new specifier(s), '
            f'skipped {skipped_count} existing. Total in DB: {total}'
        ))
