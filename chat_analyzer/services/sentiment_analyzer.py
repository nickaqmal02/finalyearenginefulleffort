import os
import logging
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch

logger = logging.getLogger(__name__)

class MalaySentimentAnalyzer:
    """XLM-RoBERTa sentiment analyzer for Malay/English mixed text"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = None
        self.is_loaded = False
        
        # Path to your trained model
        self.model_path = Path(__file__).parent.parent / 'ml_models' / 'xlm_roberta_malay'
        
        # Labels: 0=negative, 1=neutral, 2=positive
        self.labels = {
            0: 'negative',
            1: 'neutral',
            2: 'positive'
        }
        
        self.load_model()
    
    def load_model(self):
        """Load your trained XLM-RoBERTa model"""
        try:
            if not self.model_path.exists():
                logger.warning(f"Model not found at {self.model_path}")
                logger.info("Using fallback rule-based sentiment")
                self.is_loaded = False
                return
            
            # Set device (Mac M-series acceleration)
            if torch.backends.mps.is_available():
                self.device = torch.device('mps')
                logger.info("Using MPS (Apple Silicon) acceleration")
            elif torch.cuda.is_available():
                self.device = torch.device('cuda')
                logger.info("Using CUDA acceleration")
            else:
                self.device = torch.device('cpu')
                logger.info("Using CPU")
            
            # Load your trained tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(str(self.model_path))
            self.model = AutoModelForSequenceClassification.from_pretrained(str(self.model_path))
            self.model.to(self.device)
            self.model.eval()
            
            self.is_loaded = True
            logger.info(f"✅ Model loaded from {self.model_path}")
            logger.info(f"   Device: {self.device}")
            logger.info(f"   Labels: {self.labels}")
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self.is_loaded = False
    
    def analyze(self, text):
        """Analyze sentiment of a single text"""
        if not text or not text.strip():
            return 'neutral'
        
        # Fallback if model not loaded
        if not self.is_loaded:
            return self._rule_based_sentiment(text)
        
        try:
            # Tokenize
            inputs = self.tokenizer(
                text,
                return_tensors='pt',
                truncation=True,
                max_length=128,
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Predict
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.softmax(outputs.logits, dim=-1)
                predicted_class = torch.argmax(predictions, dim=-1).item()
            
            return self.labels.get(predicted_class, 'neutral')
            
        except Exception as e:
            logger.error(f"Sentiment analysis error: {e}")
            return 'neutral'
    
    def analyze_batch(self, texts):
        """Analyze sentiment for multiple texts"""
        results = []
        for text in texts:
            results.append(self.analyze(text))
        return results
    
    def _rule_based_sentiment(self, text):
        """Fallback rule-based sentiment (Malay keywords)"""
        text_lower = text.lower()
        
        positive_words = [
            'terima kasih', 'bagus', 'baik', 'puas hati', 'gembira',
            'seronok', 'membantu', 'improvement', 'progress', 'terbaik',
            'alhamdulillah', 'sangat baik', 'majuj', 'happy', 'good',
            'love', 'best', 'awesome', 'suka', 'puas'
        ]
        
        negative_words = [
            'teruk', 'buruk', 'kecewa', 'sedih', 'marah', 'tak puas',
            'masalah', 'risau', 'bimbang', 'lambat', 'tak membantu',
            'fail', 'gagal', 'menangis', 'bad', 'sad', 'angry',
            'hate', 'benci', 'kecewa', 'hampeh'
        ]
        
        positive_score = sum(1 for word in positive_words if word in text_lower)
        negative_score = sum(1 for word in negative_words if word in text_lower)
        
        if positive_score > negative_score:
            return 'positive'
        elif negative_score > positive_score:
            return 'negative'
        else:
            return 'neutral'

# Singleton instance
sentiment_analyzer = MalaySentimentAnalyzer()

def analyze_sentiment(text):
    """Convenience function to analyze sentiment"""
    return sentiment_analyzer.analyze(text)

def batch_analyze_conversations():
    """Analyze sentiment for all conversations without sentiment"""
    from ..models import Conversation
    
    conversations = Conversation.objects.filter(
        sentiment_analysis__isnull=True
    ).exclude(cleaned_text__isnull=True)
    
    count = 0
    for conv in conversations:
        text = conv.cleaned_text or conv.message
        sentiment = analyze_sentiment(text)
        conv.sentiment_analysis = sentiment
        conv.save()
        count += 1
    
    logger.info(f"Analyzed sentiment for {count} conversations")
    return count