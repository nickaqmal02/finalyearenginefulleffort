from django.core.management.base import BaseCommand
from chat_analyzer.models import Client, ClientContact
import csv
from pathlib import Path

class Command(BaseCommand):
    help = 'Migrate existing clients to have contacts '

    def add_arguments(self, parser):
        # todo : add arguments
        parser.add_argument('--csv', type=str, help='CSV file path')
        parser.add_argument('--interactive', action='store_true')
        parser.add_argument('--dry-run', action='store_true')
        # it will automatically convert --dry-run into dry_run because of argparse which is here is the parser


    def handle(self, *args, **options):
        # todo : main logic, this is where we handle all logic
        csv_file = options.get('csv')
        interactive = options.get('interactive')
        dry_run = options.get('dry_run')

        clients = Client.objects.all()
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("🔄 CLIENT CONTACT MIGRATION")
        self.stdout.write("=" * 70)

        if dry_run:
            self.stdout.write(self.style.WARNING("⚠️  DRY RUN MODE - No changes will be saved"))

        self.stdout.write(f"\n 📊 Found {clients.count()} clients ")

        if csv_file:
            self.migrate_from_csv(csv_file, dry_run) # so kita akan send kt method of migrate_from_csv first two argument
        elif interactive:
            self.migrate_interactive(clients, dry_run) # atau kita akan send dkt migrate_interactive

        # final summary 
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("✅ Migration completed!"))
        self.stdout.write(f"📊 Total contacts now: {ClientContact.objects.count()}")

        self.stdout.write("=" * 70)

    def auto_migrate(self, clients, dry_run):
        """auto migrate using username as phone number"""
        self.stdout.write("\n 📝 AUTO-MIGRATING...")

        migrated = 0
        skipped = 0

        for client in clients:
            if client.contacts.exists():
                self.stdout.write(f" {client.parent_name} - already has contacts ")
                skipped += 1
                continue

            # try to extract phone from username
            phone = self.extract_phone_from_username(client.username)

            if phone:
                if not dry_run:
                    ClientContact.objects.create(
                        client=client,
                        contact_type='father',
                        name=client.parent_name,
                        phone_number=phone,
                        is_primary=True
                    )
                migrated += 1
                self.stdout.write(self.style.SUCCESS(f"  ✅ {client.parent_name} → {phone} "))

            else:
                self.stdout.write(self.style.WARNING(f".  ⚠️ {client.parent_name} -> no phone number was found for this client "))
                skipped += 1
        
        self.stdout.write(f"\n 📊 Results: {migrated} migrated, {skipped} skipped")

    def migrate_from_csv(self, csv_path, dry_run):
        """ migrate using csv file"""
        csv_file = Path(csv_path)

        if not csv_file.exists():
            self.stdout.write(self.style.ERROR(f"File not found: {csv_path}"))
            return
            
        self.stdout.write(f"\n📄 Reading CSV from {csv_path}")

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            migrated = 0
            errors = 0

            for row in reader:
                parent_name = row.get('parent_name', '').strip()
                phone = row.get('phone_number', '').strip()
                contact_type = row.get('contact_type', 'father').strip()

                if not parent_name or not phone:
                    self.stdout.write(self.style.WARNING(f" ⚠️ INVALID ROW: {row}"))
                    errors += 1
                    continue
                client = Client.objects.filter(parent_name=parent_name).first()
                if not client:
                    self.stdout.write(self.style.WARNING(f"     ⚠️ Client not found: {parent_name}"))
                    errors += 1
                    continue
                if client.contacts.exists():
                    self.stdout.write(f"    ⏭️ {parent_name} - already has contacts")
                    continue
                if not dry_run:
                    ClientContact.objects.create(
                        client=client,
                        contact_type=contact_type,
                        name=client.parent_name,
                        phone_number=phone,
                        is_primary=True
                    )
                migrated += 1
                self.stdout.write(self.style.SUCCESS(f"     ✅ {parent_name} -> {phone}"))

            self.stdout.write(f"\n 📊 Results: {migrated} migrated, {errors} errors")

    def migrate_interactive(self, clients, dry_run):
        """interactive migration - ask user for each client"""
        self.stdout.write("\n INTERACTIVE MODE - ENTER PHONE NUMBERS \n")

        migrated = 0

        for client in clients:
            if client.contacts.exists():
                self.stdout.write(f"⏭️ {client.parent_name} - already has contacts")
                continue

            self.stdout.write(f"\n 📌 Client: {client.parent_name}")
            self.stdout.write(f"    Child: {client.child_name}")
            self.stdout.write(f"    Username: {client.username}")

            phone = input("     📞 Phone number for (or 'skip'): ").strip()

            if phone.lower() == 'skip':
                self.stdout.write("     ⏭️ Skipped")
                continue

            if phone:
                if not dry_run:
                    ClientContact.objects.create(
                        client=client,
                        contact_type='father',
                        name=client.parent_name,
                        phone_number=phone,
                        is_primary=True
                    )
                migrated += 1
                self.stdout.write(self.style.SUCCESS(f"     ✅ Added: {phone}"))

            else:
                self.stdout.write(self.style.WARNING(f"     ⚠️ No phone entered, skipped"))
                        
        self.stdout.write(f"📊 Migrated: {migrated} clients")

    def extract_phone_from_username(self, username):
        """ Try to extract phone number from username """
        # handle pattern like "nstAhmad" - cant extract phone
        # handle pattern like "0179716757"

        if username and username.isdigit():
            return username
            
        # look for phone pattern in username (e.g., "ahmad_60178767777")
        import re
        phone_match = re.search(r'(\+?[0-9]{10-15})', username)
        if phone_match:
            return phone_match.group(1)
            
        return None

                
            