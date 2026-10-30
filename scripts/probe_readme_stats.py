"""Read-only probe: project stats for README accuracy. Safe, no writes."""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finalyearengineredo.settings")
django.setup()

from django.db.models import Count  # noqa: E402

from chat_analyzer.models import (  # noqa: E402
    ChatMessage,
    Conversation,
    SessionBooking,
    Topic,
    TreatmentDocument,
    User,
)

print("USERS", User.objects.count())
print("ROLES", list(User.objects.values("role").annotate(n=Count("id"))))
print("CONVERSATIONS", Conversation.objects.count())
print("CHAT_MESSAGES", ChatMessage.objects.count())
print("BOOKINGS", SessionBooking.objects.count())
print("TREATMENT_DOCS", TreatmentDocument.objects.count())
print("TOPICS", list(Topic.objects.values_list("id", "name")[:20]))
print("TOPIC_MSG_COUNTS", list(Topic.objects.annotate(n=Count("message_topics")).values_list("name", "n")))
