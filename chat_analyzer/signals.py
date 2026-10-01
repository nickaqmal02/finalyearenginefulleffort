"""
This signals for chat_analyzer
Listens for message topics save events and updates ClientTopicScore aggregates.
DRY: one listener handles all save scenarios - no manual refresh calls needed.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg, Count
from .models import MessageTopic, ClientTopicScore

@receiver(post_save, sender=MessageTopic)
def update_client_topic_score_on_save(sender, instance, created, **kwargs):
    """
    recompute ClientTopicScore for the (client, topic) pair whenever a MessageTopic is saved.

    Uses update_or_create for idempotency 

    """
    # import inside function to avoid circular import at module level
    conv = instance.conversation

    aggregates = MessageTopic.objects.filter(
        conversation__client_id=conv.client_id,
        topic_id=instance.topic_id,
        is_primary=True,
    ).aggregate(
        avg_score=Avg('score'),
        msg_count=Count('id'),
    )

    # adding the aggregates part first
    ClientTopicScore.objects.update_or_create(
        client_id=conv.client_id,
        topic_id=instance.topic_id,
        defaults={
            'score': aggregates['avg_score'] or 0.0,
            'message_count': aggregates['msg_count'] or 0,
        }
    )
