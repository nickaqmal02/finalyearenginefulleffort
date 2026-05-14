import os
import shutil
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import cache

class Command(BaseCommand):
    help = 'Clear all cache files and temporary data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--pycache',
            action='store_true',
            help='Clear Python __pycache__ folders only'
        )
        parser.add_argument(
            '--sessions',
            action='store_true',
            help='Clear Django sessions only'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Clear everything (cache, pycache, sessions)'
        )
    
    def handle(self, *args, **options):
        self.stdout.write("=" * 50)
        self.stdout.write("🧹 CLEARING CACHE")
        self.stdout.write("=" * 50)
        
        cleared_count = 0
        
        # 1. Clear Django cache
        if options['all'] or not (options['pycache'] or options['sessions']):
            cache.clear()
            self.stdout.write(self.style.SUCCESS("✅ Django cache cleared"))
            cleared_count += 1
        
        # 2. Clear Python __pycache__ folders
        if options['pycache'] or options['all']:
            count = self.clear_pycache()
            self.stdout.write(self.style.SUCCESS(f"✅ Cleared {count} __pycache__ folders"))
            cleared_count += 1
        
        # 3. Clear Django sessions
        if options['sessions'] or options['all']:
            count = self.clear_sessions()
            self.stdout.write(self.style.SUCCESS(f"✅ Cleared {count} sessions"))
            cleared_count += 1
        
        self.stdout.write("=" * 50)
        self.stdout.write(self.style.SUCCESS(f"🎉 Cache cleared! ({cleared_count} operations)"))
        self.stdout.write("=" * 50)
    
    def clear_pycache(self):
        """Delete all __pycache__ folders"""
        count = 0
        project_root = settings.BASE_DIR
        
        for root, dirs, files in os.walk(project_root):
            if '__pycache__' in dirs:
                pycache_path = os.path.join(root, '__pycache__')
                try:
                    shutil.rmtree(pycache_path)
                    count += 1
                    self.stdout.write(f"   Deleted: {pycache_path}")
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"   Failed: {pycache_path} - {e}"))
        
        return count
    
    def clear_sessions(self):
        """Clear Django session table"""
        try:
            from django.contrib.sessions.models import Session
            count = Session.objects.count()
            Session.objects.all().delete()
            return count
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"   Sessions table error: {e}"))
            return 0