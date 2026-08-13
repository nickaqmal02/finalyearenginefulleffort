# chat_analyzer/management/commands/test_cleaner.py
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from chat_analyzer.services.text_cleaner import clean_text, get_cleaner
from chat_analyzer.models import Conversation, User
import random
from datetime import datetime, timedelta

User = get_user_model()


class Command(BaseCommand):
    help = 'Test the Malay text cleaner with sample messages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-data',
            action='store_true',
            help='Create sample Conversation data for testing'
        )
        parser.add_argument(
            '--test-only',
            action='store_true',
            help='Only test cleaning without creating data'
        )
        parser.add_argument(
            '--show-stats',
            action='store_true',
            help='Show statistics about current data'
        )

    def handle(self, *args, **options):
        if options.get('show_stats'):
            self.show_stats()
            return

        if options.get('test_only'):
            self.test_cleaner_only()
            return

        if options.get('create_data'):
            self.create_sample_data()
            self.test_cleaner_on_data()
            return

        # Default: Test with sample messages
        self.test_sample_messages()


    # ============================================
    # 1. TEST WITH SAMPLE MESSAGES
    # ============================================
    def test_sample_messages(self):
        """Test the cleaner with predefined sample messages."""
        self.stdout.write(self.style.SUCCESS('\n🧪 TESTING TEXT CLEANER WITH SAMPLE MESSAGES\n'))
        self.stdout.write('=' * 60)

        # Sample messages in Malay, English, and Manglish
        test_messages = [
            # Pure Malay
            "Saya rasa sangat 😢 tertekan hari ni😭😭😭 Tak tau nak buat apa",
            
            # English + Malay mixed
            "Hi Dr. I'm feeling very anxious today. Saya tak boleh tidur malam tadi.",
            
            # Manglish (colloquial Malaysian English)
            "Actually i feel very stress la, macam tak tau nak buat apa dah",
            
            # Pure Malay with typos
            "terimekasih byk2 for the support 👍👍 saya sgt hargai",
            
            # Therapy-specific
            "Anak saya ada masalah tantrum dan meltdown setiap hari lately",
            
            # Short messages
            "okey2 i will try the exercise 💪💪",
            
            # Emotional messages
            "Saya rasa macam nak give up dah 😢😢😢",
            
            # Mixed language
            "I need help. Anak saya sangat hyperactive dan susah nak fokus",
            
            # Long message
            "Salam Dr. Saya nak tanya pasal progress anak saya. Dia dah boleh tidur sendiri tapi masih ada masalah dengan emosi. Dia cepat marah dan selalu menangis tanpa sebab.",
            
            # Slang and abbreviations
            "sgt cemas skrg ni, tk tau nk buat apa, byk masalah family",
        ]

        self.stdout.write(f'\n📊 Testing {len(test_messages)} messages...\n')

        for i, msg in enumerate(test_messages, 1):
            cleaned = clean_text(msg)
            
            self.stdout.write(f'\n[{i}] ORIGINAL:')
            self.stdout.write(f'  "{msg}"')
            self.stdout.write(f'\n[{i}] CLEANED:')
            self.stdout.write(f'  "{cleaned}"')
            self.stdout.write('-' * 60)

        self.stdout.write(self.style.SUCCESS('\n✅ Test complete!'))


    # ============================================
    # 2. TEST ON EXISTING DATA
    # ============================================
    def test_cleaner_on_data(self):
        """Test cleaner on existing Conversation data."""
        self.stdout.write(self.style.SUCCESS('\n🧪 TESTING CLEANER ON EXISTING DATA\n'))
        self.stdout.write('=' * 60)

        conversations = Conversation.objects.filter(cleaned_text__isnull=False)
        count = conversations.count()

        if count == 0:
            self.stdout.write(self.style.WARNING('⚠️ No conversations with cleaned_text found.'))
            self.stdout.write('Run: python manage.py test_cleaner --create-data')
            return

        self.stdout.write(f'\n📊 Found {count} conversations with cleaned_text\n')

        # Sample a few to show
        sample_size = min(5, count)
        samples = random.sample(list(conversations), sample_size)

        for i, conv in enumerate(samples, 1):
            self.stdout.write(f'\n[{i}] ORIGINAL:')
            self.stdout.write(f'  "{conv.message[:100]}..."')
            self.stdout.write(f'\n[{i}] CLEANED:')
            self.stdout.write(f'  "{conv.cleaned_text[:100]}..."')
            self.stdout.write('-' * 60)

        self.stdout.write(self.style.SUCCESS(f'\n✅ Tested {sample_size} conversations!'))


    # ============================================
    # 3. CREATE SAMPLE DATA
    # ============================================
    def create_sample_data(self):
        """Create sample Conversation data for testing."""
        self.stdout.write(self.style.SUCCESS('\n📝 CREATING SAMPLE CONVERSATION DATA\n'))
        self.stdout.write('=' * 60)

        # Get or create a test client
        client, created = User.objects.get_or_create(
            username='test_client',
            defaults={
                'first_name': 'Test',
                'last_name': 'Client',
                'email': 'test@sentiri.com',
                'role': 'client',
                'phone': '+60123456789',
                'is_active': True,
            }
        )
        if created:
            client.set_password('test123')
            client.save()
            self.stdout.write('✅ Created test_client')

        # Sample messages with different patterns
        sample_messages = [
            ("Saya rasa sangat 😢 tertekan hari ni. Tak tau nak buat apa", True),
            ("Hi Dr. I'm feeling very anxious today. Saya tak boleh tidur malam tadi.", True),
            ("terimekasih byk2 for the support 👍👍 saya sgt hargai", True),
            ("Anak saya ada masalah tantrum dan meltdown setiap hari", True),
            ("okey2 i will try the exercise 💪💪", True),
            ("Saya rasa macam nak give up dah 😢😢😢", True),
            ("I need help. Anak saya sangat hyperactive dan susah nak fokus", True),
            ("sgt cemas skrg ni, tk tau nk buat apa", True),
            ("Alhamdulillah, my child is improving day by day", True),
            ("terima kasih doktor, saya rasa lebih tenang sekarang", True),
        ]

        # Create Conversation objects
        base_date = datetime.now().date()
        count = 0

        for i, (message, should_clean) in enumerate(sample_messages):
            conv, created = Conversation.objects.get_or_create(
                client=client,
                date=base_date - timedelta(days=i),
                time=datetime.now().time(),
                username='+60123456789',
                message=message,
                defaults={
                    'cleaned_text': clean_text(message) if should_clean else None,
                    'upload_batch': 'TEST_BATCH_001',
                }
            )
            if created:
                count += 1
                self.stdout.write(f'✅ Created conversation {i+1}: "{message[:30]}..."')

        self.stdout.write(self.style.SUCCESS(f'\n✅ Created {count} sample conversations!'))

        # Show stats
        self.show_stats()


    # ============================================
    # 4. SHOW STATISTICS
    # ============================================
    def show_stats(self):
        """Show statistics about current data."""
        self.stdout.write(self.style.SUCCESS('\n📊 DATA STATISTICS\n'))
        self.stdout.write('=' * 60)

        total = Conversation.objects.count()
        with_cleaned = Conversation.objects.filter(cleaned_text__isnull=False).count()
        without_cleaned = Conversation.objects.filter(cleaned_text__isnull=True).count()

        if total == 0:
            self.stdout.write(self.style.WARNING('⚠️ No conversations found!'))
            self.stdout.write('Run: python manage.py test_cleaner --create-data')
            return

        self.stdout.write(f'\n📊 Total Conversations: {total}')
        self.stdout.write(f'📊 With Cleaned Text: {with_cleaned}')
        self.stdout.write(f'📊 Without Cleaned Text: {without_cleaned}')

        if with_cleaned > 0:
            # Get a sample of cleaned text
            sample = Conversation.objects.filter(cleaned_text__isnull=False).first()
            if sample:
                self.stdout.write(f'\n📝 Sample Cleaned Text:')
                self.stdout.write(f'   ORIGINAL: "{sample.message[:80]}"')
                self.stdout.write(f'   CLEANED:  "{sample.cleaned_text[:80]}"')


    # ============================================
    # 5. TEST CLEANER ONLY (Quick Test)
    # ============================================
    def test_cleaner_only(self):
        """Quick test of the cleaner without any data dependencies."""
        self.stdout.write(self.style.SUCCESS('\n🧪 QUICK CLEANER TEST\n'))
        self.stdout.write('=' * 60)

        # Print cleaner configuration
        cleaner = get_cleaner()
        self.stdout.write(f'\n📋 Cleaner Configuration:')
        self.stdout.write(f'   Typo Mappings: {len(cleaner.typo_mapping)}')
        self.stdout.write(f'   Emoji Mappings: {len(cleaner.emoji_mapping)}')
        self.stdout.write(f'   Slang Mappings: {len(cleaner.slang_mapping)}')
        self.stdout.write(f'   Stop Words: {len(cleaner.stop_words)}')
        self.stdout.write(f'   Domain Words: {len(cleaner.domain_words)}')
        self.stdout.write(f'   Curse Words: {len(cleaner.curse_words)}')

        # Test a few messages
        test_msg = "Saya sangat 😢 tertekan hari ni. terimekasih byk2 for support!"
        cleaned = clean_text(test_msg)
        self.stdout.write(f'\n📝 Test Result:')
        self.stdout.write(f'   Original: {test_msg}')
        self.stdout.write(f'   Cleaned:  {cleaned}')

        self.stdout.write(self.style.SUCCESS('\n✅ Cleaner is working!'))
