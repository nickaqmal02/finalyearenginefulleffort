import re
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class MalayTextCleaner:
    """Text cleaner for Malay/English mixed messages"""
    
    def __init__(self):
        self.data_dir = Path(__file__).parent.parent.parent / 'data'
        self.typo_mapping = self.load_typo_mapping()
        self.stop_words = self.load_stop_words()
        self.emoji_mapping = self.load_emoji_mapping()
        
        logger.info(f"Loaded {len(self.typo_mapping)} typo mappings")
        logger.info(f"Loaded {len(self.stop_words)} stop words")
        logger.info(f"Loaded {len(self.emoji_mapping)} emoji mappings")
    
    def load_typo_mapping(self):
        """Load typo to correct word mapping"""
        typo_file = self.data_dir / 'typo_mapping.json'
        if typo_file.exists():
            with open(typo_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'terimekasih': 'terima kasih',
            'trimekasih': 'terima kasih',
            'okey': 'ok',
            'x': 'tak',
            'tk': 'tak',
            'tdk': 'tak',
            'sgt': 'sangat',
            'skrg': 'sekarang',
            'utk': 'untuk',
            'kpd': 'kepada',
            'sbb': 'sebab',
            'byk': 'banyak',
            'byk2': 'banyak',
        }
    
    def load_stop_words(self):
        """Load Malay stop words"""
        stopwords_file = self.data_dir / 'stopwords_malay.txt'
        if stopwords_file.exists():
            with open(stopwords_file, 'r', encoding='utf-8') as f:
                return set(word.strip().lower() for word in f.readlines())
        return {
            'yang', 'dan', 'di', 'ke', 'dari', 'ini', 'itu', 'untuk',
            'dengan', 'pada', 'adalah', 'ia', 'mereka', 'kita', 'kami',
            'anda', 'saya', 'aku', 'kamu', 'dia', 'kamu', 'kita', 'kami'
        }
    
    def load_emoji_mapping(self):
        """Load emoji to Malay word mapping"""
        emoji_file = self.data_dir / 'emoji_mapping.json'
        if emoji_file.exists():
            with open(emoji_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            '😊': 'seronok',
            '👍': 'terbaik',
            '😢': 'sedih',
            '❤️': 'sayang',
            '😂': 'gelak',
            '😭': 'menangis',
            '😡': 'marah',
            '😠': 'marah',
            '😍': 'sayang',
            '🎉': 'tahniah',
            '🔥': 'hebat',
            '💪': 'semangat',
            '🙏': 'terima kasih',
        }
    
    def convert_emojis(self, text):
        """Convert emojis to Malay words"""
        for emoji, word in self.emoji_mapping.items():
            if emoji in text:
                text = text.replace(emoji, f" {word} ")
        return text
    
    def fix_typos(self, text):
        """Fix common typos"""
        words = text.split()
        corrected = []
        for word in words:
            if word.lower() in self.typo_mapping:
                corrected.append(self.typo_mapping[word.lower()])
            else:
                corrected.append(word)
        return ' '.join(corrected)
    
    def remove_stopwords(self, text):
        """Remove Malay stop words"""
        words = text.split()
        filtered = [w for w in words if w.lower() not in self.stop_words]
        return ' '.join(filtered)
    
    def clean(self, text):
        """Complete text cleaning pipeline"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)
        
        # Remove mentions
        text = re.sub(r'@\w+', '', text)
        
        # Convert emojis
        text = self.convert_emojis(text)
        
        # Remove punctuation (keep letters, numbers, spaces)
        text = re.sub(r'[^\w\s]', '', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Fix typos
        text = self.fix_typos(text)
        
        # Remove stop words
        text = self.remove_stopwords(text)
        
        return text

# Singleton instance
cleaner = MalayTextCleaner()

def clean_text(text):
    """Convenience function to clean text"""
    return cleaner.clean(text)

def batch_clean_conversations():
    """Clean all conversations without cleaned_text"""
    from ..models import Conversation
    
    conversations = Conversation.objects.filter(cleaned_text__isnull=True)
    count = 0
    for conv in conversations:
        conv.cleaned_text = clean_text(conv.message)
        conv.save()
        count += 1
    
    logger.info(f"Cleaned {count} conversations")
    return count