# chat_analyzer/services/text_cleaner.py
import json
import logging
import re
from pathlib import Path

from django.db.models import Q

logger = logging.getLogger(__name__)

class MalayTextCleaner:
    """Multi-purpose text cleaner for Malay/English mixed messages"""

    def __init__(self, data_dir=None):
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / 'data'
        else:
            self.data_dir = Path(data_dir)

        # Load all data files
        self.typo_mapping = self.load_json('typo_mapping.json')
        self.emoji_mapping = self.load_json('emoji_mapping.json')
        self.slang_mapping = self.load_json('slang_mapping.json')
        self.curse_words = self.load_curse_words()

        # Load domain words (therapy-specific terms to KEEP)
        self.domain_words = self.load_domain_words()

        # Load sentiment-specific stopwords (LIGHT)
        self.sentiment_stopwords = self.load_sentiment_stopwords()

        # Load topic-specific stopwords (HEAVY)
        self.topic_stopwords = self.load_topic_stopwords()

        # Combine all mappings
        self.all_mappings = {**self.typo_mapping, **self.slang_mapping}

        logger.info(f"✅ Loaded {len(self.typo_mapping)} typo mappings")
        logger.info(f"✅ Loaded {len(self.emoji_mapping)} emoji mappings")
        logger.info(f"✅ Loaded {len(self.slang_mapping)} slang mappings")
        logger.info(f"✅ Loaded {len(self.domain_words)} domain words")
        logger.info(f"✅ Loaded {len(self.sentiment_stopwords)} sentiment stopwords")
        logger.info(f"✅ Loaded {len(self.topic_stopwords)} topic stopwords")
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

    def load_domain_words(self):
        """Load therapy-specific domain words with comment support."""
        filepath = self.data_dir / 'domain_words.txt'
        domain_words = set()

        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        if line:
                            domain_words.add(line.lower())
        else:
            logger.warning(f"Domain words file not found: {filepath}")
            # Default domain words (therapy-related)
            domain_words = {
                'terapi', 'rawatan', 'sesi', 'perundingan', 'kaunseling',
                'perkembangan', 'pertuturan', 'bahasa', 'komunikasi',
                'sosial', 'emosi', 'fizikal', 'motor', 'kognitif',
                'autisme', 'adhd', 'tantrum', 'sensory', 'integrasi',
                'rangsangan', 'permainan', 'aktiviti', 'latihan',
                'sebut', 'sebutan', 'perkataan', 'ayat', 'huruf',
                'gembira', 'sedih', 'marah', 'takut', 'risau',
                'perasaan', 'keyakinan', 'motivasi', 'semangat'
            }

        return domain_words

    def load_sentiment_stopwords(self):
        """Load LIGHT stopwords for sentiment analysis."""
        filepath = self.data_dir / 'sentiment_stopwords.txt'
        stopwords = set()

        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        if line:
                            stopwords.add(line.lower())
        else:
            logger.warning(f"Sentiment stopwords file not found: {filepath}")
            # Default light stopwords
            stopwords = {
                'yang', 'dan', 'di', 'ke', 'dari', 'pada', 'ini', 'itu',
                'untuk', 'dengan', 'tanpa', 'oleh', 'sebagai', 'kepada',
                'dalam', 'ada', 'juga', 'lagi', 'sahaja', 'seperti',
                'saya', 'kamu', 'aku', 'dia', 'mereka', 'kami', 'kita',
                'aku', 'kau', 'mu', 'ku', 'kepada', 'daripada'
            }

        return stopwords

    def load_topic_stopwords(self):
        """Load HEAVY stopwords for topic modeling."""
        filepath = self.data_dir / 'topic_stopwords.txt'
        stopwords = set()

        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        if line:
                            stopwords.add(line.lower())
        else:
            logger.warning(f"Topic stopwords file not found: {filepath}")
            # Default heavy stopwords
            stopwords = {
                # Start with sentiment stopwords
                'yang', 'dan', 'di', 'ke', 'dari', 'pada', 'ini', 'itu',
                'untuk', 'dengan', 'tanpa', 'oleh', 'sebagai', 'kepada',
                'dalam', 'ada', 'juga', 'lagi', 'sahaja', 'seperti',
                'saya', 'kamu', 'aku', 'dia', 'mereka', 'kami', 'kita',

                # Greetings
                'assalamualaikum', 'waalaikumussalam', 'salam', 'selamat',
                'pagi', 'petang', 'malam', 'hello', 'hi', 'hai',

                # Thank you
                'terima', 'kasih', 'thanks', 'thank', 'tq',

                # Names
                'maya', 'arif', 'anita', 'haziq', 'danial',

                # Intensifiers (remove for topic modeling)
                'sangat', 'terlalu', 'amat', 'paling', 'begitu', 'demikian',
                'banyak', 'sedikit', 'masih', 'sudah', 'dah',

                # Common verbs
                'buat', 'latihan', 'main', 'makan', 'minum',
                'tidur', 'bangun', 'mandi', 'pakai', 'pergi', 'datang',
                'cuba', 'bagus', 'baik', 'hebat', 'wah',
                'semoga', 'berbangga', 'harapan',

                # Pronouns and family
                'anak', 'ibu', 'ayah', 'bapa', 'mak', 'emak',
                'abang', 'kakak', 'adik', 'anak', 'anak',
            }

        return stopwords

    def load_curse_words(self):
        """Load curse words for filtering with comment support."""
        filepath = self.data_dir / 'curse_words.txt'
        curse_words = set()

        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        if line:
                            curse_words.add(line.lower())
        else:
            logger.warning(f"Curse words file not found: {filepath}")

        return curse_words

    def _base_clean(self, text):
        """Base cleaning applied to all texts."""
        if not text:
            return ""

        # Lowercase
        text = text.lower()

        # Remove URLs
        text = re.sub(r'http\S+|www\S+|https\S+', '', text)

        # Remove mentions
        text = re.sub(r'@\w+', '', text)

        # Convert emojis
        text = self.convert_emojis(text)

        # Fix typos and slang
        text = self.fix_mappings(text)

        # Filter curse words
        text = self.filter_curse_words(text)

        # Remove extra whitespace
        text = ' '.join(text.split())

        return text

    def clean_for_sentiment(self, text):
        """Clean text for sentiment analysis.
        - Keeps punctuation (!, ?) for emotion
        - Keeps intensifiers (sangat, terlalu)
        - Keeps emotional words
        - Only removes structural words
        """
        if not text:
            return ""

        # Base cleaning
        text = self._base_clean(text)

        # FOR SENTIMENT: Keep punctuation for emotion detection
        text = re.sub(r'[^\w\s!?]', '', text)

        # Remove light stopwords (sentiment-specific)
        words = text.split()
        filtered = []
        for word in words:
            # ALWAYS keep domain words (therapy terms)
            if word in self.domain_words:
                filtered.append(word)
                continue
            # Keep if not in sentiment stopwords
            if word not in self.sentiment_stopwords and len(word) > 1:
                filtered.append(word)

        return ' '.join(filtered)

    def clean_for_topic_modeling(self, text):
        """Clean text for topic modeling.
        - Removes ALL stopwords aggressively
        - Removes greetings, names, fillers
        - Keeps only content words
        """
        if not text:
            return ""

        # Base cleaning
        text = self._base_clean(text)

        # FOR TOPIC MODELING: Remove all punctuation
        text = re.sub(r'[^\w\s]', '', text)

        # Remove heavy stopwords (topic modeling)
        words = text.split()
        filtered = []
        for word in words:
            # ALWAYS keep domain words (they ARE the topics we want)
            if word in self.domain_words:
                filtered.append(word)
                continue
            # Remove if in topic stopwords or too short
            if word not in self.topic_stopwords and len(word) > 2:
                filtered.append(word)

        return ' '.join(filtered)

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

def clean_for_sentiment(text):
    """Clean text for sentiment analysis."""
    return get_cleaner().clean_for_sentiment(text)

def clean_for_topic_modeling(text):
    """Clean text for topic modeling."""
    return get_cleaner().clean_for_topic_modeling(text)

def clean_text(text, aggressive=False):
    """Legacy function for backward compatibility."""
    if aggressive:
        return clean_for_topic_modeling(text)
    return clean_for_sentiment(text)


def batch_clean_conversations():
    """Clean all conversations for both sentiment and topic modeling."""
    from ..models import Conversation

    cleaner = get_cleaner()
    conversations = Conversation.objects.filter(
        Q(is_cleaned_sentiment=False) | Q(is_cleaned_topic=False)
    )

    sentiment_count = 0
    topic_count = 0

    for conv in conversations:
        # Clean for sentiment
        if not conv.is_cleaned_sentiment:
            conv.cleaned_text = cleaner.clean_for_sentiment(conv.message)
            conv.is_cleaned_sentiment = True
            sentiment_count += 1

        # Clean for topic modeling
        if not conv.is_cleaned_topic:
            conv.cleaned_text_topic = cleaner.clean_for_topic_modeling(conv.message)
            conv.is_cleaned_topic = True
            topic_count += 1

        conv.save()

    logger.info(f"✅ Cleaned {sentiment_count} messages for sentiment")
    logger.info(f"✅ Cleaned {topic_count} messages for topic modeling")
    return sentiment_count, topic_count
