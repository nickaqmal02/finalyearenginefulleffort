# chat_analyzer/services/topic_modeler.py
import re
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from collections import Counter
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import joblib
from django.utils import timezone

logger = logging.getLogger(__name__)


class MalayTopicModeler:
    """Topic modeling for Malay/English therapy conversations using BERTopic."""
    
    def __init__(self):
        self.topic_model = None
        self.embedding_model = None
        self.vectorizer = None
        self.is_loaded = False
        
        # Model path
        self.model_path = Path(__file__).parent.parent / 'ml_models' / 'topic_model'
        
        # ✅ Malay stopwords (extended for therapy domain)
        self.malay_stopwords = self._load_stopwords()
        
        # ✅ Domain-specific stopwords
        self.domain_stopwords = [
            'nak', 'tu', 'ni', 'je', 'lah', 'kah', 'kan', 'yer', 'ya',
            'saya', 'kamu', 'aku', 'dia', 'mereka', 'kami', 'kita',
            'yang', 'dan', 'di', 'ke', 'dari', 'pada', 'ini', 'itu',
            'untuk', 'dengan', 'tanpa', 'oleh', 'sebagai', 'kepada',
            'dalam', 'ada', 'juga', 'lagi', 'sahaja', 'seperti',
            'mohon', 'tolong', 'maaf', 'ok', 'okay', 'dekat', 'dekat'
        ]
    
    def _load_stopwords(self):
        """Load Malay stopwords from data file or use default."""
        stopwords_path = Path(__file__).parent.parent / 'data' / 'stopwords_malay.txt'
        if stopwords_path.exists():
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                return set(word.strip() for word in f.readlines() if word.strip())
        return {
            'yang', 'dan', 'di', 'ke', 'dari', 'pada', 'ini', 'itu',
            'untuk', 'dengan', 'tanpa', 'oleh', 'sebagai', 'kepada',
            'dalam', 'ada', 'juga', 'lagi', 'sahaja', 'seperti',
            'saya', 'kamu', 'aku', 'dia', 'mereka', 'kami', 'kita'
        }
    
    def setup_models(self):
        """Load embedding model and setup BERTopic."""
        try:
            # ✅ Check for MPS (Apple Silicon)
            import torch
            if torch.backends.mps.is_available():
                device = 'mps'
                print("✅ Using MPS (Apple Silicon) for embeddings")
            elif torch.cuda.is_available():
                device = 'cuda'
                print("✅ Using CUDA for embeddings")
            else:
                device = 'cpu'
                print("⚠️ Using CPU for embeddings (slower)")
            
            # ✅ Load XLMR-BERT for embeddings
            self.embedding_model = SentenceTransformer(
                'xlm-roberta-large',
                device=device
            )
            print(f"✅ XLMR-BERT embedding model loaded on {device}")
            
            # ✅ Custom vectorizer with Malay stopwords
            all_stopwords = list(self.malay_stopwords.union(set(self.domain_stopwords)))
            
self.vectorizer = CountVectorizer(
                stop_words=all_stopwords,
                ngram_range=(1, 3),
                min_df=2,
                max_df=0.85
            )
            print(f"✅ Vectorizer configured with {len(all_stopwords)} stopwords")
            
            # ✅ Create BERTopic model
            self.topic_model = BERTopic(
                embedding_model=self.embedding_model,
                vectorizer_model=self.vectorizer,
                language='multilingual',
                min_topic_size=3,
                n_gram_range=(1, 3),
                calculate_probabilities=True,
                verbose=True
            )
            print("✅ BERTopic model configured")
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"❌ Error setting up models: {e}")
            self.is_loaded = False
            return False
    
    def preprocess_messages(self, messages):
        """Preprocess messages for topic modeling."""
        # Remove empty or very short messages
        messages = [msg for msg in messages if msg and len(msg.strip()) > 5]
        
        # Remove duplicates (keep first occurrence)
        seen = set()
        unique_messages = []
        for msg in messages:
            msg_clean = msg.strip().lower()
            if msg_clean not in seen:
                seen.add(msg_clean)
                unique_messages.append(msg)
        
        print(f"✅ Preprocessed: {len(unique_messages)} unique messages from {len(messages)} total")
        return unique_messages
    
    def train(self, messages, min_topic_size=3):
        """Train the topic model on messages."""
        
        print("\n" + "="*60)
        print("🧠 TOPIC MODELING TRAINING")
        print("="*60)
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        if not self.is_loaded:
            print("⚠️ Models not loaded, setting up...")
            if not self.setup_models():
                print("❌ Failed to setup models")
                return None
        
        # Preprocess messages
        messages = self.preprocess_messages(messages)
        
        if len(messages) < 10:
            print(f"❌ Not enough messages for topic modeling ({len(messages)} messages, need at least 10)")
            return None
        
        print(f"📊 Training on {len(messages)} messages")
        print(f"   Min topic size: {min_topic_size}")
        
        # ✅ Train the model
        print("\n🔄 Training BERTopic model (this may take a few minutes)...")
        
        try:
            self.topic_model.min_topic_size = min_topic_size
            topics, probabilities = self.topic_model.fit_transform(messages)
            
            # Get topic info
            topic_info = self.topic_model.get_topic_info()
            num_topics = len(topic_info[topic_info['Topic'] != -1])
            
            print(f"\n✅ Discovered {num_topics} topics from {len(messages)} messages")
            
            # Show discovered topics
            print("\n📋 Discovered Topics:")
            for idx, row in topic_info.iterrows():
                if row['Topic'] != -1:
                    topic_name = self.get_topic_name(row['Topic'])
                    print(f"   Topic {row['Topic']}: {topic_name} ({row['Count']} messages)")
            
            # ✅ Save the model
            self.save_model()
            
            return {
                'topics': topics,
                'probabilities': probabilities,
                'topic_info': topic_info,
                'num_topics': num_topics,
                'messages': messages
            }
            
        except Exception as e:
            print(f"❌ Error training model: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_topic_name(self, topic_id):
        """Get a human-readable name for a topic."""
        if topic_id == -1:
            return "Outliers"
        
        keywords = self.topic_model.get_topic(topic_id)
        if not keywords:
            return f"Topic_{topic_id}"
        
        # Use top 3 keywords as topic name
        top_keywords = [word for word, _ in keywords[:3]]
        return " - ".join(top_keywords)
    
    def save_model(self):
        """Save the trained topic model."""
        if not self.topic_model:
            print("❌ No model to save")
            return
        
        self.model_path.mkdir(parents=True, exist_ok=True)
        self.topic_model.save(str(self.model_path))
        print(f"✅ Model saved to {self.model_path}")
    
    def load_model(self):
        """Load a saved topic model."""
        try:
            if self.model_path.exists():
                self.topic_model = BERTopic.load(str(self.model_path))
                print(f"✅ Model loaded from {self.model_path}")
                return True
            else:
                print(f"⚠️ No model found at {self.model_path}")
                return False
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False
    
    def save_topics_to_db(self, topics, probabilities, messages):
        """Save discovered topics to Django database."""
        from chat_analyzer.models import Topic, ClientTopicScore, TopicTrend, MessageTopic, Conversation
        
        print("\n💾 Saving topics to database...")
        
        # Get unique topic IDs
        unique_topics = set([t for t in topics if t != -1])
        
        for topic_id in unique_topics:
            keywords = self.topic_model.get_topic(topic_id)
            if not keywords:
                continue
            
            # Get top keywords
            top_keywords = [word for word, _ in keywords[:10]]
            topic_name = " - ".join([word for word, _ in keywords[:3]])
            
            # ✅ Save to Topic table
            topic_obj, created = Topic.objects.get_or_create(
                name=topic_name[:100],
                defaults={
                    'description': f"Topic discovered from therapy conversations",
                    'keywords': top_keywords,
                    'is_active': True
                }
            )
            
            if created:
                print(f"   ✅ Created topic: {topic_name}")
            else:
                print(f"   🔄 Updated topic: {topic_name}")
                topic_obj.keywords = top_keywords
                topic_obj.save()
            
            # ✅ Link messages to topics
            # Get messages for this topic
            topic_messages = [msg for idx, msg in enumerate(messages) if topics[idx] == topic_id]
            
            for msg in topic_messages[:20]:  # Limit per topic for performance
                try:
                    # Find the conversation by cleaned_text (approximate match)
                    conversation = Conversation.objects.filter(
                        cleaned_text__icontains=msg[:50]
                    ).first()
                    
                    if conversation:
                        MessageTopic.objects.get_or_create(
                            conversation=conversation,
                            topic=topic_obj,
                            defaults={
                                'score': 0.5,  # Can calculate exact score
                                'confidence': 0.5
                            }
                        )
                except Exception as e:
                    print(f"   ⚠️ Error linking message: {e}")
        
        print(f"✅ Saved {len(unique_topics)} topics to database")
        return len(unique_topics)
    
    def generate_topic_report(self, messages, topics):
        """Generate a report of discovered topics."""
        report = {
            'total_messages': len(messages),
            'total_topics': len(set([t for t in topics if t != -1])),
            'outliers': sum(1 for t in topics if t == -1),
            'topics': []
        }
        
        topic_info = self.topic_model.get_topic_info()
        for idx, row in topic_info.iterrows():
            if row['Topic'] != -1:
                keywords = self.topic_model.get_topic(row['Topic'])
                report['topics'].append({
                    'id': row['Topic'],
                    'name': self.get_topic_name(row['Topic']),
                    'count': row['Count'],
                    'keywords': [word for word, _ in keywords[:10]],
                    'scores': [round(score, 3) for _, score in keywords[:10]]
                })
        
        return report


# ============================================
# SINGLETON INSTANCE
# ============================================
_topic_modeler = None


def get_topic_modeler():
    """Get or create the topic modeler singleton."""
    global _topic_modeler
    if _topic_modeler is None:
        _topic_modeler = MalayTopicModeler()
    return _topic_modeler


def train_topics(messages=None, min_topic_size=3):
    """Train topic model on messages."""
    from chat_analyzer.models import Conversation
    
    if messages is None:
        # Get all messages from database
        messages = list(Conversation.objects.filter(
            cleaned_text__isnull=False
        ).exclude(
            cleaned_text=''
        ).values_list('cleaned_text', flat=True))
    
    if len(messages) == 0:
        print("❌ No messages found in database!")
        return None
    
    modeler = get_topic_modeler()
    result = modeler.train(messages, min_topic_size)
    
    if result:
        modeler.save_topics_to_db(
            result['topics'],
            result['probabilities'],
            result['messages']
        )
        
        # Generate report
        report = modeler.generate_topic_report(
            result['messages'],
            result['topics']
        )
        
        print("\n📊 TOPIC MODELING REPORT")
        print("="*60)
        print(f"Total Messages: {report['total_messages']}")
        print(f"Topics Discovered: {report['total_topics']}")
        print(f"Outliers: {report['outliers']}")
        print("\n📋 Topics:")
        for topic in report['topics']:
            print(f"   {topic['id']}: {topic['name']} ({topic['count']} messages)")
            print(f"      Keywords: {', '.join(topic['keywords'][:5])")
    
    return result




### training the topic modeling
# Basic training (uses all messages)
python manage.py train_topics

# With custom min topic size
python manage.py train_topics --min-topic-size 5

# With limit (for testing)
python manage.py train_topics --limit 500

# Clear existing topics first
python manage.py train_topics --clear
