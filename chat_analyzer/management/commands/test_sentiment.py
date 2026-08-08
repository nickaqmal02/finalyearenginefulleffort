from django.core.management.base import BaseCommand
from chat_analyzer.services.sentiment_analyzer import analyze_sentiment

class Command(BaseCommand):
    help = 'Test sentiment analysis with sample Malay messages'

    def add_arguments(self, parser):
        parser.add_argument(
            '--text',
            type=str,
            help='Single message to analyze'
        )
        parser.add_argument(
            '--batch',
            action='store_true',
            help='Run batch test with predefined messages'
        )
        parser.add_argument(
            '--message',
            type=str,
            help='Alternative to --text'
        )

    def handle(self, *args, **options):
        text = options.get('text') or options.get('message')
        
        if text:
            # Single message mode
            self.test_single(text)
        elif options.get('batch'):
            # Batch test mode
            self.test_batch()
        else:
            # Interactive mode
            self.test_interactive()

    def test_single(self, text):
        """Test a single message"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🔍 SINGLE MESSAGE ANALYSIS")
        self.stdout.write("=" * 60)
        self.stdout.write(f"📝 Message: {text}")
        
        result = analyze_sentiment(text)
        
        # Color coding based on sentiment
        if result == 'positive':
            color = self.style.SUCCESS
            emoji = "😊"
        elif result == 'negative':
            color = self.style.ERROR
            emoji = "😞"
        else:
            color = self.style.WARNING
            emoji = "😐"
        
        self.stdout.write(color(f"\n🎯 Sentiment: {emoji} {result.upper()}"))
        self.stdout.write("=" * 60)

    def test_batch(self):
        """Test with predefined batch of messages"""
        test_messages = [
            ("Terima kasih cikgu! Anak saya semakin baik", "positive"),
            ("Saya kecewa dengan perkhidmatan ini", "negative"),
            ("Bila sesi terapi seterusnya?", "neutral"),
            ("Alhamdulillah, sangat berpuas hati!", "positive"),
            ("Saya tidak berpuas hati, teruk sangat", "negative"),
            ("Ok, terima kasih", "positive"),
            ("Saya risau anak saya lambat bercakap", "negative"),
            ("Boleh saya tahu harga untuk sesi tambahan?", "neutral"),
            ("Terbaik! Recommended sangat", "positive"),
            ("Service sangat lambat dan tidak profesional", "negative"),
        ]
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write("🧪 BATCH SENTIMENT TEST")
        self.stdout.write("=" * 70)
        self.stdout.write(f"{'EXPECTED':<12} {'PREDICTED':<12} {'RESULT':<10} MESSAGE")
        self.stdout.write("-" * 70)
        
        correct = 0
        total = len(test_messages)
        
        for msg, expected in test_messages:
            predicted = analyze_sentiment(msg)
            is_correct = predicted == expected
            
            if is_correct:
                correct += 1
                result_icon = self.style.SUCCESS("✅")
            else:
                result_icon = self.style.ERROR("❌")
            
            # Color based on prediction
            if predicted == 'positive':
                predicted_colored = self.style.SUCCESS(predicted)
            elif predicted == 'negative':
                predicted_colored = self.style.ERROR(predicted)
            else:
                predicted_colored = self.style.WARNING(predicted)
            
            expected_colored = self.style.SUCCESS(expected) if is_correct else self.style.ERROR(expected)
            
            self.stdout.write(f"{expected_colored:<12} {predicted_colored:<12} {result_icon:<10} {msg[:50]}...")
        
        self.stdout.write("-" * 70)
        
        # Summary
        accuracy = (correct / total) * 100
        if accuracy >= 80:
            summary_style = self.style.SUCCESS
        elif accuracy >= 60:
            summary_style = self.style.WARNING
        else:
            summary_style = self.style.ERROR
        
        self.stdout.write(summary_style(f"\n📊 ACCURACY: {correct}/{total} ({accuracy:.1f}%)"))
        self.stdout.write("=" * 70)

    def test_interactive(self):
        """Interactive mode - keep asking for messages"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🤖 INTERACTIVE SENTIMENT TESTER")
        self.stdout.write("=" * 60)
        self.stdout.write("Type a message in Malay or English, or 'quit' to exit\n")
        
        while True:
            try:
                user_input = input("📝 Enter message: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.stdout.write(self.style.SUCCESS("\n👋 Goodbye!"))
                    break
                
                if not user_input:
                    continue
                
                result = analyze_sentiment(user_input)
                
                if result == 'positive':
                    emoji = "😊"
                    color = self.style.SUCCESS
                elif result == 'negative':
                    emoji = "😞"
                    color = self.style.ERROR
                else:
                    emoji = "😐"
                    color = self.style.WARNING
                
                self.stdout.write(color(f"\n🎯 Sentiment: {emoji} {result.upper()}\n"))
                
            except KeyboardInterrupt:
                self.stdout.write(self.style.SUCCESS("\n\n👋 Goodbye!"))
                break
            except EOFError:
                break


# Also create a simple version for quick testing
class CommandSimple(Command):
    """Alias for quick testing"""
    pass