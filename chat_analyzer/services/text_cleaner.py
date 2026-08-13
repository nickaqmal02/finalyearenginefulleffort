# chat_analyzer/services/text_cleaner.py
import re
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class MalayTextCleaner:
    """Text cleaner for Malay/English mixed messages"""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / 'data'
        else:
            self.data_dir = Path(data_dir)
        
        # Load all data files
        self.typo_mapping = self.load_json('typo_mapping.json')
        self.emoji_mapping = self.load_json('emoji_mapping.json')
        self.slang_mapping = self.load_json('slang_mapping.json')
        self.stop_words = self.load_stop_words()
        self.domain_words = self.load_domain_words()
        self.curse_words = self.load_curse_words()
        
        # Combine all mappings
        self.all_mappings = {**self.typo_mapping, **self.slang_mapping}
        
        logger.info(f"✅ Loaded {len(self.typo_mapping)} typo mappings")
        logger.info(f"✅ Loaded {len(self.emoji_mapping)} emoji mappings")
        logger.info(f"✅ Loaded {len(self.slang_mapping)} slang mappings")
        logger.info(f"✅ Loaded {len(self.stop_words)} stop words")
        logger.info(f"✅ Loaded {len(self.domain_words)} domain words")
        logger.info(f"✅ Loaded {len(self.curse_words)} curse words")
    
    def load_json(self, filename):
        """Load JSON data file."""
        filepath = self.data_dir / filename
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                try:
                    return json.load(f)
                except json.JSONDecodeError:
                    logger.error(f"Error loading {filename}")
                    return {}
        else:
            logger.warning(f"File not found: {filename}")
            return {}
    
    def load_stop_words(self):
        """Load Malay stop words."""
        filepath = self.data_dir / 'stopwords_malay.txt'
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return set(word.strip().lower() for word in f.readlines() if word.strip())
        return set()
    
    def load_domain_words(self):
        """Load therapy-specific domain words."""
        filepath = self.data_dir / 'domain_words.txt'
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                words = []
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        words.append(line.lower())
                return set(words)
        return set()
    
    def load_curse_words(self):
        """Load curse words for filtering."""
        filepath = self.data_dir / 'curse_words.txt'
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return set(word.strip().lower() for word in f.readlines() if word.strip())
        return set()
    
    def convert_emojis(self, text):
        """Convert emojis to Malay words."""
        for emoji, word in self.emoji_mapping.items():
            if emoji in text:
                text = text.replace(emoji, f" {word} ")
        return text
    
    def fix_mappings(self, text):
        """Fix typos and slang."""
        words = text.split()
        corrected = []
        for word in words:
            lower_word = word.lower()
            if lower_word in self.all_mappings:
                corrected.append(self.all_mappings[lower_word])
            else:
                corrected.append(word)
        return ' '.join(corrected)
    
    def filter_curse_words(self, text):
        """Filter curse words."""
        words = text.split()
        filtered = []
        for word in words:
            if word.lower() not in self.curse_words:
                filtered.append(word)
        return ' '.join(filtered)
    
    def remove_stopwords(self, text):
        """Remove Malay stop words."""
        words = text.split()
        filtered = []
        for word in words:
            lower_word = word.lower()
            # Keep domain words even if they're in stopwords
            if lower_word not in self.stop_words or lower_word in self.domain_words:
                filtered.append(word)
        return ' '.join(filtered)
    
    def clean(self, text):
        """Complete text cleaning pipeline."""
        if not text:
            return ""
        
        # 1. Convert to lowercase
        text = text.lower()
        
        # 2. Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        
        # 3. Remove mentions
        text = re.sub(r'@\w+', '', text)
        
        # 4. Convert emojis
        text = self.convert_emojis(text)
        
        # 5. Remove special characters (keep letters, numbers, spaces)
        text = re.sub(r'[^\w\s]', '', text)
        
        # 6. Remove extra whitespace
        text = ' '.join(text.split())
        
        # 7. Fix typos and slang
        text = self.fix_mappings(text)
        
        # 8. Filter curse words
        text = self.filter_curse_words(text)
        
        # 9. Remove stop words (except domain words)
        text = self.remove_stopwords(text)
        
        # 10. Remove extra whitespace again
        text = ' '.join(text.split())
        
        return text


# ============================================
# Singleton instance
# ============================================
_cleaner = None


def get_cleaner():
    """Get or create the cleaner singleton."""
    global _cleaner
    if _cleaner is None:
        _cleaner = MalayTextCleaner()
    return _cleaner


def clean_text(text):
    """Convenience function to clean text."""
    cleaner = get_cleaner()
    return cleaner.clean(text)


def batch_clean_conversations():
    """Clean all conversations without cleaned_text."""
    from ..models import Conversation
    
    cleaner = get_cleaner()
    conversations = Conversation.objects.filter(cleaned_text__isnull=True)
    count = 0
    for conv in conversations:
        conv.cleaned_text = cleaner.clean(conv.message)
        conv.save()
        count += 1
    
    logger.info(f"✅ Cleaned {count} conversations")
    return count
