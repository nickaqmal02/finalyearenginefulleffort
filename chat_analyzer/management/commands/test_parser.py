import os
from django.core.management.base import BaseCommand
from chat_analyzer.services.whatsapp_parser import parse_whatsapp_file

class Command(BaseCommand):
    help = 'Test WhatsApp parser with sample file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to WhatsApp .txt file to parse'
        )
    
    def handle(self, *args, **options):
        file_path = options.get('file')
        
        if file_path:
            if not os.path.exists(file_path):
                self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            # Use your actual format
            self.stdout.write(self.style.WARNING('No file provided, using sample...'))
            content = """[13/10/2024, 23:23:42] akmal hilmi tsc upnm: sebb dah gerakkan number tu masa normalize
[13/10/2024, 23:23:58] Topex: esok bincang dalam kelas, tengok cmne
[13/10/2024, 23:24:45] Topex: asalnya aku darab 23 kali je, bila dah normalize...fraction berkurangan
[13/10/2024, 23:25:43] +60 16-935 4580: yg x dpt lagi pm pm
[13/10/2024, 23:49:35] Jacknan tsc upnm: math math yg kureng ni
[14/10/2024, 07:33:03] nick: tingkat 4 bangunan lestari dewan kuliah 2"""
        
        # Parse the content
        messages = parse_whatsapp_file(content)
        
        # Display results
        self.stdout.write(self.style.SUCCESS(f"\n✅ Parsed {len(messages)} messages\n"))
        self.stdout.write("=" * 70)
        
        for i, msg in enumerate(messages[:20], 1):
            self.stdout.write(f"\n📝 Message {i}:")
            self.stdout.write(f"   Date: {msg['date']}")
            self.stdout.write(f"   Time: {msg['time']}")
            self.stdout.write(f"   From: {msg['username']}")
            preview = msg['message'][:80] + '...' if len(msg['message']) > 80 else msg['message']
            self.stdout.write(f"   Text: {preview}")
        
        if len(messages) > 20:
            self.stdout.write(f"\n... and {len(messages) - 20} more messages")
        
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("✅ Test complete!"))