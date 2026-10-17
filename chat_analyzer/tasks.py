"""Celery tasks for delayed ML analysis on live chat messages.

Flow:
  1. Client sends a ChatMessage in the view
  2. View creates a Conversation row (sentiment=None, topic=None)
  3. View fires: analyze_live_message.delay(conversation_id)  ← 5-min countdown starts
  4. Celery worker picks up the task after 5 minutes
  5. Runs the SAME pipeline functions used for WhatsApp data:
     clean_for_sentiment → analyze_sentiment → clean_for_topic_modeling → TopicMapper
  6. Writes results back to the Conversation row + creates MessageTopic links

Only client messages get analyzed. Therapist replies are is_from_client=False
and excluded from topic mapping (same exclusion logic as WhatsApp staff messages).
"""

import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # if ML model fails, retry in 1 min
)
def analyze_live_message(self, conversation_id):
    """
    Delayed ML analysis for a single live-chat message.

    Called from views.py: analyze_live_message.delay(conv_id)
    Celery holds it for 5 minutes (countdown=300 set at call site),
    then the worker runs this function.

    Args:
        conversation_id: The Conversation row created when the client sent the chat message.
    """
    from chat_analyzer.models import Conversation, Topic, MessageTopic
    from chat_analyzer.services.text_cleaner import clean_for_sentiment, clean_for_topic_modeling
    from chat_analyzer.services.sentiment_analyzer import analyze_sentiment
    from chat_analyzer.services.topic_mapper import TopicMapper

    try:
        conv = Conversation.objects.select_related('client').get(id=conversation_id)
    except Conversation.DoesNotExist:
        logger.error(f"Conversation #{conversation_id} not found — task dropped")
        return {'status': 'error', 'reason': 'conversation_not_found'}

    # Skip if already analyzed (idempotency — safe to retry)
    if conv.sentiment is not None:
        logger.info(f"Conversation #{conversation_id} already analyzed — skipping")
        return {'status': 'skipped', 'reason': 'already_analyzed'}

    raw_text = conv.message
    logger.info(f"Analyzing Conversation #{conversation_id}: {raw_text[:50]}...")

    # ── STEP 1: Clean for sentiment (light — preserves emotion) ──
    cleaned_sentiment = clean_for_sentiment(raw_text)
    conv.cleaned_text = cleaned_sentiment
    conv.is_cleaned_sentiment = True

    # ── STEP 2: Sentiment analysis (XLM-RoBERTa inference) ──
    result = analyze_sentiment(cleaned_sentiment)
    conv.sentiment = result.get('label', 'neutral')
    conv.sentiment_score = result.get('score', 0.0)
    conv.sentiment_confidence = result.get('confidence', 0.0)

    # ── STEP 3: Clean for topic modeling (aggressive — removes stopwords) ──
    cleaned_topic = clean_for_topic_modeling(raw_text)
    conv.cleaned_text_topic = cleaned_topic
    conv.is_cleaned_topic = True

    # Save what we have so far (sentiment + cleaned text)
    conv.save()
    logger.info(
        f"  Sentiment: {conv.sentiment} ({conv.sentiment_score:+.2f}) "
        f"conf={conv.sentiment_confidence:.2f}"
    )

    # ── STEP 4: Topic mapping (against the 5 frozen active topics) ──
    # Only map client messages — therapist replies are excluded from topics
    if not conv.is_from_client:
        logger.info(f"  Staff message — topic mapping skipped")
        conv.is_processed = True
        conv.save()
        return {
            'status': 'ok',
            'conversation_id': conversation_id,
            'sentiment': conv.sentiment,
            'topics': 'skipped (staff message)',
        }

    # Get the 5 active topics
    defined_topics = list(Topic.objects.filter(is_active=True, status='active'))
    if not defined_topics:
        logger.warning("No active topics found — skipping topic mapping")
        conv.is_processed = True
        conv.save()
        return {
            'status': 'ok',
            'conversation_id': conversation_id,
            'sentiment': conv.sentiment,
            'topics': 'none (no active topics)',
        }

    # Use the same TopicMapper your batch pipeline uses
    mapper = TopicMapper()
    matches = mapper.map_message_with_alternatives(
        cleaned_topic,
        defined_topics,
        threshold=mapper.threshold * 0.5,  # same lowered threshold as outliers in train_topics
    )

    if not matches:
        logger.info(f"  No topics matched for: {cleaned_topic[:50]}")
        conv.is_processed = True
        conv.save()
        return {
            'status': 'ok',
            'conversation_id': conversation_id,
            'sentiment': conv.sentiment,
            'topics': 'none (no match above threshold)',
        }

    # Write MessageTopic rows (same pattern as topic_modeler.py)
    for match in matches:
        MessageTopic.objects.update_or_create(
            conversation=conv,
            topic=match['topic'],
            defaults={
                'score': match['score'],
                'confidence': match.get('confidence', 0.5),
                'is_primary': match.get('is_primary', False),
            }
        )

    topic_names = [f"{m['topic'].name}{'*' if m.get('is_primary') else ''}" for m in matches]
    logger.info(f"  Topics: {', '.join(topic_names)}")

    conv.is_processed = True
    conv.save()

    return {
        'status': 'ok',
        'conversation_id': conversation_id,
        'sentiment': conv.sentiment,
        'sentiment_score': conv.sentiment_score,
        'topics': topic_names,
    }


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def ingest_treatment_document(self, document_id):
    """
    Async document ingestion: PDF → chunks → embeddings → ChromaDB.

    Called from views when a doctor uploads a treatment document.
    The heavy work (PDF parsing + embedding) runs in Celery, not in the request.
    """
    from chat_analyzer.models import TreatmentDocument
    from chat_analyzer.services.rag_service import ingest_document
    from django.utils import timezone

    try:
        doc = TreatmentDocument.objects.get(id=document_id)
    except TreatmentDocument.DoesNotExist:
        logger.error(f"TreatmentDocument #{document_id} not found")
        return {'status': 'error', 'reason': 'document_not_found'}

    if doc.status == 'ready':
        logger.info(f"TreatmentDocument #{document_id} already ingested — skipping")
        return {'status': 'skipped', 'reason': 'already_ready'}

    # Mark as processing
    doc.status = 'processing'
    doc.save()

    try:
        result = ingest_document(doc.file.path, doc.title)

        if result['status'] == 'ready':
            doc.status = 'ready'
            doc.chunks_created = result['chunks_created']
            doc.processed_at = timezone.now()
            doc.error_message = ''
            doc.save()
            logger.info(f"Document #{document_id} ingested: {result['chunks_created']} chunks")
            return result
        else:
            doc.status = 'failed'
            doc.error_message = result.get('error', 'Unknown error')
            doc.save()
            raise Exception(result.get('error'))

    except Exception as e:
        doc.status = 'failed'
        doc.error_message = str(e)
        doc.save()
        logger.error(f"Ingestion failed for #{document_id}: {e}")
        raise self.retry(exc=e)
