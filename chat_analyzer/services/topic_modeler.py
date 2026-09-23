# chat_analyzer/services/topic_modeler.py
import logging
from datetime import datetime
from pathlib import Path
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import CountVectorizer
from umap import UMAP
from chat_analyzer.services.text_cleaner import clean_for_topic_modeling

logger = logging.getLogger(__name__)

class MalayTopicModeler:
    """Topic modeling for malay/english therapy conversations using BERTopic"""

    def __init__(self):
        self.topic_model = None
        self.embedding_model = None
        self.vectorizer = None
        self.is_loaded = False

        # model path
        self.model_path = Path(__file__).parent.parent / 'ml_models' / 'topic_model'

        # Topic-specific stopwords (aggressive filtering)
        self.topic_stopwords = self._load_topic_stopwords()

        # Domain words (therapy-specific terms to KEEP)
        self.domain_words = self._load_domain_words()

    def _load_topic_stopwords(self):
        """Load aggressive stopwords for topic modeling."""
        stopwords = set()
        stopwords_path = Path(__file__).parent.parent / 'data' / 'topic_stopwords.txt'

        if stopwords_path.exists():
            with open(stopwords_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        if line:
                            stopwords.add(line.lower())
        else:
            # Fallback stopwords if file doesn't exist
            stopwords = {
                # Structural
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

                # Intensifiers
                'sangat', 'terlalu', 'amat', 'paling', 'begitu', 'demikian',
                'banyak', 'sedikit', 'masih', 'sudah', 'dah', 'tak', 'tidak',

                # Fillers
                'nak', 'tu', 'ni', 'je', 'lah', 'kah', 'kan', 'yer', 'ya', 'oh', 'ah', 'eh'
            }

        print(f"✅ Loaded {len(stopwords)} topic stopwords")
        return stopwords

    def _load_domain_words(self):
        """Load therapy-specific domain words to KEEP."""
        domain_words = set()
        domain_path = Path(__file__).parent.parent / 'data' / 'domain_words_topic.txt'

        if domain_path.exists():
            with open(domain_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '#' in line:
                            line = line.split('#')[0].strip()
                        if line:
                            domain_words.add(line.lower())
        else:
            # Fallback domain words
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

        print(f"✅ Loaded {len(domain_words)} domain words")
        return domain_words

    def preprocess_messages(self, messages):
        """Preprocess messages for topic modeling with aggressive cleaning."""
        processed = []

        for msg in messages:
            if not msg:
                continue
            cleaned = msg.strip()

            # skip the word if too shorts
            if len(cleaned.split()) >= 1:
                processed.append(cleaned)

        # Remove duplicates
        seen = set()
        unique_messages = []
        for msg in processed:
            if msg not in seen:
                seen.add(msg)
                unique_messages.append(msg)

        print(f"✅ Preprocessed: {len(unique_messages)} unique messages from {len(messages)} total")
        return unique_messages

    def setup_models(self):
        """Load embedding model and setup BERTopic"""
        try:
            # check for mps (Apple Silicon)
            import torch
            if torch.backends.mps.is_available():
                device = 'mps'
                print('using MPS (Apple Silicon) for embeddings')
            elif torch.cuda.is_available():
                device = 'cuda'
                print('using CUDA for embeddings')
            else:
                device = 'cpu'
                print('using CPU might be slower')

            # load XLMR-BERT for embeddings
            self.embedding_model = SentenceTransformer(
                'xlm-roberta-large',
                device=device
            )
            print(f"    XLMR-BERT embedding model loaded on {device}")

            # custom vectorizer with stopwords
            all_stopwords = list(self.topic_stopwords)

            self.vectorizer = CountVectorizer(
                stop_words=all_stopwords, # filter all stopwords
                ngram_range=(1, 2), # detecting words like anxiety attacks
                min_df=2, # keep words appearing in >= 2 cluster documents (run 7: middle ground — 3 hid tidur, 1 collapsed clusters) 
                max_df=0.75, # ignore words too common 
                max_features=500 # keep that top 500 words
            )
            print(f"✅ Vectorizer configured with {len(all_stopwords)} stopwords")

            # create the BERTopic model
            self.topic_model = BERTopic(
                embedding_model=self.embedding_model, #XLMRobertaModel
                vectorizer_model=self.vectorizer, # refer above
                umap_model=UMAP(
                    n_neighbors=15,
                    n_components=5,
                    min_dist=0.0,
                    metric="cosine",
                    random_state=42
                ),
                language='multilingual', # telling that hey this is not just malay
                min_topic_size=5, # HBDSCAN we only draw circle if around an island if it has at least 5 messages crammed togetehr
                n_gram_range=(1, 2), # same as above 
                calculate_probabilities=True, # give fuzzy membership value for every message
                verbose=True # make the bertopic talk while training 
            )
            print('✅ BERTopic model configured')

            self.is_loaded = True
            return True

        except Exception as e:
            print(f"❌ Error setting up models: {e}")
            self.is_loaded = False
            return False

    def train(self, messages=None, min_topic_size=5, use_db_messages=True):
        """
        Train the topic model on messages.

        Args:
            messages: List of messages (if None, will fetch from DB)
            min_topic_size: Minimum size of topics
            use_db_messages: If True, fetch from DB using cleaned_text_topic field
        """
        print("\n" + "=" * 60)
        print("🧠 TRAINING TOPIC MODELING")
        print("=" * 60)
        print(f" Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Get messages from database if not provided
        if messages is None and use_db_messages:
            from chat_analyzer.models import Conversation

            # Try to use cleaned_text_topic first
            messages = list(
                Conversation.objects.filter(
                    cleaned_text_topic__isnull=False
                ).exclude(
                    cleaned_text_topic=''
                ).values_list('cleaned_text_topic', flat=True)
            )

            # Fallback to cleaned_text if topic field doesn't exist
            # NOTE: cleaned_text is sentiment-cleaned, NOT topic-cleaned —
            # re-apply topic cleaning here since preprocess no longer cleans.
            if not messages:
                print("⚠️ No topic-cleaned messages found, falling back to cleaned_text")
                messages = [
                    clean_for_topic_modeling(m)
                    for m in Conversation.objects.filter(
                        cleaned_text__isnull=False
                    ).exclude(
                        cleaned_text=''
                    ).values_list('cleaned_text', flat=True)
                    if m
                ]

            # If still no messages, fallback to raw messages
            # Raw message = uncleaned, must apply topic cleaning here too.
            if not messages:
                print("⚠️ No cleaned messages found, using raw messages")
                messages = [
                    clean_for_topic_modeling(m)
                    for m in Conversation.objects.filter(
                        message__isnull=False
                    ).exclude(
                        message=''
                    ).values_list('message', flat=True)
                    if m
                ]

        if not messages or len(messages) == 0:
            print("❌ No messages found!")
            return None

        if not self.is_loaded:
            print(" Model is loaded Mate :)))) ready for training bruh ......")
            if not self.setup_models():
                print("❌ Failed to setup models")
                return None

        # preprocess_messages with aggressive cleaning
        # pairs in: {conversation_id, text} -- dedupe by text, always remember all ids
        # declaring some dict
        text_to_ids = {}

        for conv_id, text in messages:
            key = text.strip().lower()
            if not key:
                continue
            text_to_ids.setdefault(key, []).append(conv_id)

        texts = self.preprocess_messages(list(text_to_ids.keys()))

        if len(texts) < 10:
            print(f"❌ Not enough messages for topic modeling ({len(texts)}) messages, need at least 10")
            return None

        print(f" Training on {len(texts)} messages")
        print(f"    Min topic size: {min_topic_size}")

        # train the model
        print("\n Training the BERTopic model (this may take a few minutes) .... ")

        try:
            self.topic_model.min_topic_size = min_topic_size
            topics, probabilities = self.topic_model.fit_transform(texts)

            # get the topic info
            topic_info = self.topic_model.get_topic_info()
            num_topics = len(topic_info[topic_info['Topic'] != -1])

            print(f"\n✅ Discovered {num_topics} topics from {len(messages)} messages")

            # show discovered topics
            print("\n📑 Discovered Topics:")
            for idx, row in topic_info.iterrows():
                if row['Topic'] != -1:
                    topic_name = self.get_topic_name(row['Topic'])
                    print(f"    Topic {row['Topic']}: {topic_name} ({row['Count']} messages)")

            # save the model
            self.save_model()

            return {
                'topics': topics,
                'probabilities': probabilities,
                'topic_info': topic_info,
                'num_topics': num_topics,
                'messages': texts,
                'text_to_ids': text_to_ids,
            }

        except Exception as e:
            print(f"❌ Error training model: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_topic_name(self, topic_id):
        """Get cleaner human readable name for topic."""
        if topic_id == -1:
            return "Outliers"

        keywords = self.topic_model.get_topic(topic_id)
        if not keywords:
            return f"Topic_{topic_id}"

        # Filter out stopwords from topic names
        stopwords = self.topic_stopwords
        domain_words = self.domain_words

        filtered_keywords = []

        for word, score in keywords[:10]:
            word_lower = word.lower()

            # Keep domain words and non-stopwords
            if word_lower in domain_words:
                filtered_keywords.append((word, score))
            elif word_lower not in stopwords and len(word) > 2:
                filtered_keywords.append((word, score))

            if len(filtered_keywords) >= 3:
                break

        # If no filtered keywords, use the top ones
        if not filtered_keywords:
            filtered_keywords = keywords[:3]

        return " - ".join([word for word, _ in filtered_keywords])

    def save_model(self):
        """Save the trained topic model"""
        if not self.topic_model:
            print("❌ No model to save")
            return

        try:
            # Create directory if it doesn't exist
            self.model_path.mkdir(parents=True, exist_ok=True)

            # Save to a file INSIDE the directory
            model_file = self.model_path / 'topic_model.pkl'
            self.topic_model.save(str(model_file))
            print(f"✅ Model saved to {model_file}")
        except Exception as e:
            print(f"❌ Error saving model: {e}")
            import traceback
            traceback.print_exc()

    def load_model(self):
        """Load a saved topic model if already have it"""
        try:
            model_file = self.model_path / 'topic_model.pkl'
            if model_file.exists():
                self.topic_model = BERTopic.load(str(model_file))
                print(f"✅ Model loaded from {model_file}")
                self.is_loaded = True
                return True
            else:
                print(f"☢️ No model found at {model_file}")
                return False
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            import traceback
            traceback.print_exc()
            return False

    def save_topics_to_db(self, topics, probabilities, messages, text_to_ids=None):
        """
        Save topics to database with better filtering.
        updating multi topic for each messages
        """
        from chat_analyzer.models import Conversation, MessageTopic, Topic
        from chat_analyzer.services.topic_mapper import TopicMapper

        print("\n💾 Saving topics to database... ")

        unique_topics = set([t for t in topics if t != -1])
        self.mapper = TopicMapper(threshold=1.5, min_gap=1.0)
        defined_topics = list(Topic.objects.filter(is_active=True))

        # ╔════════════════════════════════════════════╗ 
        # ║  PHASE 1: MAP EACH CLUSTER TO THE TOPICS   ║ 
        # ╚════════════════════════════════════════════╝ 
        # THIS WHOLE THINGS WAS MADE UP FROM HBDSCAN
        cluster_mapping = {}
        for topic_id in unique_topics:
            keywords = self.topic_model.get_topic(topic_id)
            if not keywords:
                continue
            
            # get all matching topics for this cluster
            matches = self.mapper.map_cluster_with_alternatives(
                keywords,
                defined_topics,
            )

            if matches:
                cluster_mapping[topic_id] = matches
                print(f"    Topic {topic_id}: {len(matches)} matching topics")
            else:
                # nothing match then we discovered topic
                fallback_keywords = [word for word, _ in keywords[:5] if word.strip()]
                topic_name = "-".join(fallback_keywords[:3])

                topic_obj, created = Topic.objects.get_or_create(
                    name=topic_name[:100],
                    defaults={
                        'description': "Topic discovered from therapy center conversations",
                        'keywords': fallback_keywords,
                        'is_active': True,
                    }
                )
                cluster_mapping[topic_id] = [{
                    'topic': topic_obj,
                    'score': 2.0,
                    'confidence': 0.5,
                    'is_primary': True,
                }]
                print(f"    Topic {topic_id} -> NEW Discovered: '{topic_obj.name}'")

        # ╔════════════════════════════════════════════╗ 
        # ║   PHASE 2: ASSIGN TOPICS TO EACH MESSAGE   ║ 
        # ╚════════════════════════════════════════════╝ 
        # the stats dictionary below still empty but we only declare the key
        stats = {
            'total': len(messages),
            'assigned': 0,
            'outliers': 0,
            'multi_topic': 0,
            'total_assignments': 0,
            'rows_written': 0,
        }

        all_ids = [cid for ids in (text_to_ids or {}).values() for cid in ids]
        conv_map = Conversation.objects.in_bulk(all_ids)
        unmapped_ids = set(all_ids)

        for idx, msg in enumerate(messages):
            topic_id = topics[idx]

            stats['total_assignments'] += 1

            # Case 1: This message belongs to a cluster
            if topic_id != -1 and topic_id in cluster_mapping:
                matches = cluster_mapping[topic_id]
            # case 2 outliers try door 1 fallback
            else:
                stats['outliers'] += 1
                # use this new method we create
                matches = self.mapper.map_message_with_alternatives(
                    msg, defined_topics,
                    threshold=self.mapper.threshold * 0.5
                ) or []
                
            if not matches:
                continue # stays unmapped_ids if not mathc

            stats['assigned'] += 1
            if len(matches) > 1:
                stats['multi_topic'] += 1

            # we expand: which is EVERY DB row sharing this text gets the topics
            for conv_id in conv_ids:
                conv = conv_map.get(conv_id)
                if conv is None:
                    continue
                unmapped_ids.discard(conv_id)
                stats['rows_written'] += 1
                for match in matches:
                    MessageTopic.objects.get_or_create(
                        conversation=conv,
                        topic=match['topic'],
                        defaults={
                            'score': match['score'],
                            'confidence': match.get('confidence', 0.5),
                            'is_primary': match.get('is_primary', False),
                        }
                    )
        # ╔════════════════════════════════════════════╗ 
        # ║        PHASE 3: Print summary             ║ 
        # ╚════════════════════════════════════════════╝ 
        # ✅ MOVED OUTSIDE THE TOPIC LOOP!
        print(f"\n📊 Multi-Topic Assignment Summary:")
        print(f"    Total messages: {stats['total']}")
        print(f"    Messages with topics: {stats['assigned']} ({stats['assigned']/stats['total']*100:.1f}%)")
        print(f"    Outliers: {stats['outliers']} ({stats['outliers']/stats['total']*100:.1f}%)")
        print(f"    Multi-topic messages: {stats['multi_topic']}")
        print(f"    Total topic assignments: {stats['total_assignments']}")

    def generate_topic_report(self, messages, topics):
        """Generate a report of discovered topics."""
        report = {
            'total': len(messages),
            'total_topics': len(set([t for t in topics if t != -1])),
            'outliers': sum(1 for t in topics if t == -1),
            'topics': []
        }

        topic_info = self.topic_model.get_topic_info()
        
        # idx means that which messages that we are talking about right now
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

    def analyze_new_messages(self, messages):
        """Analyze new messages and assign topics."""
        if not self.is_loaded:
            if not self.load_model():
                print("❌ No model loaded")
                return None

        # Clean messages for topic modeling
        cleaned_messages = [clean_for_topic_modeling(msg) for msg in messages if msg]

        # Transform to topics
        topics, probs = self.topic_model.transform(cleaned_messages)

        return {
            'topics': topics,
            'probabilities': probs,
            'messages': messages,
            'cleaned_messages': cleaned_messages
        }


# SINGLETON INSTANCE
_topic_modeler = None

def get_topic_modeler():
    """Get or create the topic modeler singleton."""
    global _topic_modeler
    if _topic_modeler is None:
        _topic_modeler = MalayTopicModeler()
    return _topic_modeler

def train_topics(messages=None, min_topic_size=5, use_db_messages=True):
    """
    Train topic model on messages.

    Args:
        messages: List of messages (if None, will fetch from DB)
        min_topic_size: Minimum size of topics
        use_db_messages: If True, fetch from DB using cleaned_text_topic field
    """
    from chat_analyzer.models import Conversation

    # If messages not provided, fetch from database
    if messages is None and use_db_messages:
        # Try to use cleaned_text_topic first (topic modeling specific cleaning)
        messages = list(
            Conversation.objects.filter(
                cleaned_text_topic__isnull=False
            ).exclude(
                cleaned_text_topic=''
            ).values_list('cleaned_text_topic', flat=True)
        )

        # Fallback to cleaned_text (sentiment cleaning)
        if not messages:
            print("⚠️ No topic-cleaned messages found, falling back to cleaned_text")
            messages = list(
                Conversation.objects.filter(
                    cleaned_text__isnull=False
                ).exclude(
                    cleaned_text=''
                ).values_list('cleaned_text', flat=True)
            )

        # Final fallback to raw messages
        if not messages:
            print("⚠️ No cleaned messages found, using raw messages")
            messages = list(
                Conversation.objects.filter(
                    message__isnull=False
                ).exclude(
                    message=''
                ).values_list('message', flat=True)
            )

    if not messages or len(messages) == 0:
        print("❌ No messages found in database!")
        return None

    modeler = get_topic_modeler()
    result = modeler.train(messages, min_topic_size)

    if result:
        modeler.save_topics_to_db(
            result['topics'],
            result['probabilities'],
            result['messages'],
            result['text_to_ids'],
        )

        # Generate report
        report = modeler.generate_topic_report(
            result['messages'],
            result['topics']
        )

        print("\n" + "=" * 60)
        print("📊 TOPIC MODELING REPORT")
        print("=" * 60)
        print(f"Total Messages: {report['total']}")
        print(f"Topics Discovered: {report['total_topics']}")
        print(f"Outliers: {report['outliers']}")
        print("\n📑 Topics:")
        for topic in report['topics']:
            print(f"    {topic['id']}: {topic['name']} ({topic['count']} messages)")
            print(f"    Keywords: {', '.join(topic['keywords'][:5])}")
        print("=" * 60)

    return result

def analyze_topics_for_messages(messages):
    """Analyze new messages using existing topic model."""
    modeler = get_topic_modeler()
    if not modeler.is_loaded:
        if not modeler.load_model():
            print("❌ No model loaded. Please train first.")
            return None
    return modeler.analyze_new_messages(messages)
