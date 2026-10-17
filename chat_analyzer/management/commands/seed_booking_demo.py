"""Seed demo booking data for the n8n reservation chatbot.

Usage:
    python manage.py seed_booking_demo

Creates:
  - StaffSchedule (Mon-Fri 9-5, Sat/Sun off) for all therapists + doctors
  - StaffTimeOff (one sample sick day per staff)
  - SessionBooking (one sample confirmed booking)
  - Prints a cheat-sheet of IDs for the n8n workflow
"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from chat_analyzer.models import User, StaffSchedule, StaffTimeOff, SessionBooking


class Command(BaseCommand):
    help = "Seed demo booking data for the n8n reservation chatbot"

    def handle(self, *args, **options):
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n══════════════════════════════════════════════"
            "\n  SEEDING BOOKING DEMO DATA"
            "\n══════════════════════════════════════════════"
        ))

        # ── 1. StaffSchedule for all therapists + doctors ──
        staff = list(User.objects.filter(role__in=['therapist', 'doctor'], is_active=True))
        self.stdout.write(f"\nFound {len(staff)} staff members")

        for s in staff:
            # Mon-Fri: 9-5, available
            for day in range(5):
                StaffSchedule.objects.get_or_create(
                    staff=s, day_of_week=day,
                    defaults={'start_time': '09:00', 'end_time': '17:00', 'is_available': True}
                )
            # Sat-Sun: off
            for day in [5, 6]:
                StaffSchedule.objects.get_or_create(
                    staff=s, day_of_week=day,
                    defaults={'start_time': '09:00', 'end_time': '17:00', 'is_available': False}
                )

        total_schedules = StaffSchedule.objects.count()
        self.stdout.write(self.style.SUCCESS(f"  ✅ Schedules: {total_schedules} rows ({len(staff)} staff × 7 days)"))

        # ── 2. StaffTimeOff (one random sick day in the next 2 weeks) ──
        for s in staff:
            sick_day = date.today() + timedelta(days=random.randint(3, 14))
            StaffTimeOff.objects.get_or_create(
                staff=s, date=sick_day,
                defaults={'reason': 'Sick leave (demo)'}
            )

        total_timeoff = StaffTimeOff.objects.count()
        self.stdout.write(self.style.SUCCESS(f"  ✅ Time-off: {total_timeoff} entries"))

        # ── 3. One sample confirmed booking ──
        client = User.objects.filter(role='client', is_active=True).first()
        therapist = User.objects.filter(role='therapist', is_active=True).first()
        if client and therapist:
            next_tuesday = date.today() + timedelta(days=(1 - date.today().weekday()) % 7)
            if next_tuesday <= date.today():
                next_tuesday += timedelta(days=7)

            booking, created = SessionBooking.objects.get_or_create(
                client=client, staff=therapist,
                date=next_tuesday,
                defaults={
                    'start_time': '10:00',
                    'end_time': '11:00',
                    'status': 'confirmed',
                    'notes': 'Demo booking from seed command',
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"  ✅ Sample booking: {client.get_full_name()} → {therapist.get_full_name()} on {next_tuesday} at 10:00"
                ))
            else:
                self.stdout.write(f"  ℹ️  Sample booking already exists for {therapist.username} on {next_tuesday}")

        # ── 4. Cheat-sheet for n8n ──
        self.stdout.write(self.style.MIGRATE_HEADING(
            "\n══════════════════════════════════════════════"
            "\n  DEMO CHEAT-SHEET (use these IDs in n8n)"
            "\n══════════════════════════════════════════════"
        ))
        self.stdout.write("\n── STAFF ──")
        for s in staff:
            self.stdout.write(f"  staff_id={s.id:<3} | {s.role:<9} | {s.username:<15} | {s.get_full_name()}")

        self.stdout.write("\n── CLIENTS ──")
        for c in User.objects.filter(role='client', is_active=True):
            th = c.assigned_therapist
            self.stdout.write(
                f"  client_id={c.id:<3} | {c.username:<15} | {c.get_full_name():<25} | "
                f"therapist={th.username if th else 'None'} (id={th.id if th else 'None'})"
            )

        self.stdout.write("\n── SAMPLE TEST MESSAGES ──")
        self.stdout.write("  'Is my therapist available next Tuesday at 3pm?'")
        self.stdout.write("  'Book a session with Aina on 2026-10-20 at 15:00'")
        self.stdout.write("  'What are my upcoming sessions?'")
        self.stdout.write("  'When does Aina work?'")

        self.stdout.write("\n── n8n WEBHOOK PAYLOAD ──")
        self.stdout.write('  {"message": "Book session with Aina on Tuesday at 3pm", "client_id": 10, "staff_id": 4}')
        self.stdout.write("\n")
