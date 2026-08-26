# chat_analyzer/management/commands/train_topics.py
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Q
from chat_analyzer.models import Conversation, Topic, ClientTopicScore, TopicTrend, MessageTopic
from chat_analyzer.services.topic_modeler import get_topic_modeler, train_topics
from chat_analyzer.services.text_cleaner import batch_clean_conversations

class Command(BaseCommand):
    help = 'Train topic model on existing Conversations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-topic-size',
            type=int,
            default=5,
            help='Minimum messages to form a topic (default: 5)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of messages to process'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing topics before training'
        )
        parser.add_argument(
            '--use-raw',
            action='store_true',
            help='Use raw messages instead of cleaned (not recommended)'
        )
        parser.add_argument(
            '--clean-first',
            action='store_true',
            help='Clean messages for topic modeling before training'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
    
    def handle(self, *args, **options):
        min_topic_size = options['min_topic_size']
        limit = options.get('limit')
        clear_existing = options.get('clear', False)
        use_raw = options.get('use_raw', False)
        clean_first = options.get('clean_first', False)
        verbose = options.get('verbose', False)

        self.stdout.write(self.style.SUCCESS('\n🧠 TRAINING TOPIC MODEL\n'))
        self.stdout.write('=' * 60)

        # Clean messages for topic modeling if requested
        if clean_first:
            self.stdout.write('🧹 Cleaning messages for topic modeling...')
            sentiment_count, topic_count = batch_clean_conversations()
            self.stdout.write(f'✅ Cleaned {topic_count} messages for topic modeling')
            self.stdout.write(f'✅ Cleaned {sentiment_count} messages for sentiment')

        # Get messages with clean text
        if use_raw:
            # Use raw messages (not recommended)
            messages_qs = Conversation.objects.filter(
                message__isnull=False
            ).exclude(
                message=''
            )
            field_name = 'message'
            self.stdout.write(self.style.WARNING('⚠️ Using raw messages (not recommended for topic modeling)'))
        else:
            # Try to use cleaned_text_topic first (topic modeling specific cleaning)
            messages_qs = Conversation.objects.filter(
                Q(cleaned_text_topic__isnull=False) & 
                ~Q(cleaned_text_topic='')
            )
            field_name = 'cleaned_text_topic'
            
            # Fallback to cleaned_text if no topic-cleaned messages
            if messages_qs.count() == 0:
                self.stdout.write(self.style.WARNING('⚠️ No topic-cleaned messages found, falling back to cleaned_text'))
                messages_qs = Conversation.objects.filter(
                    Q(cleaned_text__isnull=False) & 
                    ~Q(cleaned_text='')
                )
                field_name = 'cleaned_text'
            
            # Final fallback to raw messages
            if messages_qs.count() == 0:
                self.stdout.write(self.style.WARNING('⚠️ No cleaned messages found, falling back to raw messages'))
                messages_qs = Conversation.objects.filter(
                    Q(message__isnull=False) & 
                    ~Q(message='')
                )
                field_name = 'message'

        # Apply limit if specified
        if limit:
            messages_qs = messages_qs[:limit]

        total = messages_qs.count()

        if total == 0:
            self.stdout.write(self.style.ERROR('❌ No messages found! Please upload chats first.'))
            return

        self.stdout.write(f'📊 Found {total} messages using field: {field_name}')

        # Clear existing topics if requested
        if clear_existing:
            self.stdout.write('🗑️ Clearing existing topics...')
            with transaction.atomic():
                Topic.objects.all().delete()
                ClientTopicScore.objects.all().delete()
                TopicTrend.objects.all().delete()
                MessageTopic.objects.all().delete()
            self.stdout.write('✅ Existing topics cleared')

        # Show sample of messages for debugging
        if verbose:
            self.stdout.write('\n📝 Sample messages being used:')
            sample_messages = messages_qs.values_list(field_name, flat=True)[:5]
            for i, msg in enumerate(sample_messages, 1):
                preview = msg[:100] + '...' if len(msg) > 100 else msg
                self.stdout.write(f'    {i}. {preview}')

        # Train topics
        self.stdout.write(f'\n🚀 Training topics with min size {min_topic_size}')
        self.stdout.write('   This may take a few minutes...\n')

        # Get messages as list
        messages = list(messages_qs.values_list(field_name, flat=True))

        result = train_topics(
            messages=messages,
            min_topic_size=min_topic_size
        )

        # Show results
        if result:
            self.stdout.write(self.style.SUCCESS('\n✅ Topic modeling complete!'))

            # Show discovered topics from database
            from chat_analyzer.models import Topic
            topics = Topic.objects.filter(is_active=True)
            
            self.stdout.write(f'\n📑 Discovered {topics.count()} topics:')
            self.stdout.write('-' * 40)
            
            for topic in topics:
                self.stdout.write(f'    🏷️  {topic.name}')
                if verbose:
                    keywords = ', '.join(topic.keywords[:5]) if topic.keywords else 'No keywords'
                    self.stdout.write(f'       Keywords: {keywords}')
                self.stdout.write('')

            # Show statistics
            if result.get('topic_info') is not None:
                topic_info = result['topic_info']
                outliers = topic_info[topic_info['Topic'] == -1]
                if len(outliers) > 0:
                    outlier_count = outliers.iloc[0]['Count']
                    self.stdout.write(f'📊 Outlier messages: {outlier_count} (messages that didn\'t fit any topic)')

            # Show top topics with message counts
            self.stdout.write('\n📊 Topic Distribution:')
            sorted_topics = topics.order_by('?')[:5]  # Show 5 random topics
            for topic in sorted_topics:
                count = MessageTopic.objects.filter(topic=topic).count()
                self.stdout.write(f'    {topic.name[:40]}: {count} messages')

        else:
            self.stdout.write(self.style.ERROR('\n❌ Topic modeling failed!'))
            self.stdout.write('   Check the error messages above for details.')

        # Show next steps
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Next Steps:'))
        self.stdout.write('   1. Check the topics above to ensure they make sense')
        self.stdout.write('   2. Run `python manage.py analyze_sentiment` to analyze sentiment')
        self.stdout.write('   3. View topics in the admin panel at /admin/chat_analyzer/topic/')
        self.stdout.write('=' * 60)
