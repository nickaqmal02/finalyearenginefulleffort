"""Context processors — run on EVERY page load to inject shared template variables.

This is how the navbar unread badge works on every page, not just the chat page.
"""

from django.db.models import Sum


def unread_counts(request):
    """Inject unread message counts into every template's context."""
    if not hasattr(request, 'user') or not request.user.is_authenticated:
        return {}

    from chat_analyzer.models import ChatThread

    if request.user.role == 'therapist':
        total = ChatThread.objects.filter(
            therapist=request.user
        ).aggregate(total=Sum('therapist_unread'))['total'] or 0
        return {'unread_therapist_messages_count': total}

    elif request.user.role == 'doctor':
        total = ChatThread.objects.filter(
            doctor=request.user
        ).aggregate(total=Sum('doctor_unread'))['total'] or 0
        return {'unread_doctor_messages_count': total}

    elif request.user.role == 'client':
        total = ChatThread.objects.filter(
            client=request.user
        ).aggregate(total=Sum('client_unread'))['total'] or 0
        return {'unread_client_messages_count': total}

    return {}
