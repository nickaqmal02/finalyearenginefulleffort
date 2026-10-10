"""
here where we compute all data and 
the data will be passed to the admin index template
"""
import json
from django.db.models import Count, Q
from .models import (
    User, Conversation, Topic, MessageTopic, DiagnosisDocument,
)

def dashboard_callback(request, context):
    """
    Called by unfold before rendering admin/index.html.
    Add stats and cohort data to the template 
    """
    # KPI counts
    context["total_clients"] = User.objects.filter(role="client", is_active=True).count()
    context["total_conversations"] = Conversation.objects.count()
    context["total_topics"] = Topic.objects.filter(status="active").count()
    context["total_documents"] = DiagnosisDocument.objects.count()

    # Cohort data: Topic * Sentiment Matrix
    topic_stats = (
        MessageTopic.objects
        .filter(topic__status="active", is_primary=True)
        .values("topic__name")
        .annotate(
            total=Count("id"),
            positive=Count("id", filter=Q(conversation__sentiment="positive")),
            negative=Count("id", filter=Q(conversation__sentiment="negative")),
            neutral=Count("id", filter=Q(conversation__sentiment="neutral")),
        )
        .order_by("-total")
    )

    # build the cohort data structure for unfold
    cohort_data = {
        "headers": [
            {"title": "Positive", "subtitle": "😊"},
            {"title": "Negative", "subtitle": "😕"},
            {"title": "Neutral", "subtitle": "😑"},
            {"title": "Total", "subtitle": " "},
        ],
        "rows": [],
    }

    for stat in topic_stats:
        cohort_data["rows"].append({
            "header": {
                "title": stat["topic__name"],
                "subtitle": f"{stat['total']} messages",
            },
            "cols": [
                {"value": str(stat["positive"]), "color": "bg-green-100 border border-green-300 rounded-xl"},
                {"value": str(stat["negative"]), "color": "bg-red-100 border border-red-300 rounded-xl"},
                {"value": str(stat["neutral"]), "color": "bg-gray-100 border border-gray-300 rounded-xl"},
                {"value": str(stat["total"]), "color": "bg-blue-50 border border-blue-200 rounded-xl"},
            ],
        })

    # doughtnut chart data setup
    sentiment_totals =(
        Conversation.objects
        .filter(sentiment__isnull=False)
        .values('sentiment')
        .annotate(count=Count('id'))
        .order_by('sentiment')
    )
    # creating the hash map dictionary for faster execution
    sentiment_map = {s['sentiment']: s['count'] for s in sentiment_totals}
    context["sentiment_doughnut"] = json.dumps({
        "labels": ["Positive", "Negative", "Neutral"],
        "datasets": [{
            "data": [
                sentiment_map.get('positive', 0),
                sentiment_map.get('negative', 0),
                sentiment_map.get('neutral', 0),
            ],
            "backgroundColor": ["#10b981", "#ef4444", "#9ca3af"],
        }],
    })

    # radar chart data: topic distribution
    topic_dist = (
        MessageTopic.objects
        .filter(topic__status='active', is_primary=True)
        .values('topic__name')
        .annotate(count=Count('id'))
        .order_by('-count')
    )

    context["topic_radar"]=json.dumps({
        "labels": [t['topic__name'] for t in topic_dist],
        "datasets": [{
            "label": "Messages per Topic",
            "data": [t['count'] for t in topic_dist],
            "backgroundColor": "rgba(16, 185, 129, 0.2)",
            "borderColor": "#10b981",
            "pointBackgroundColor": "#10b981",
        }],
    })

    context["topic_sentiment_data"] = cohort_data

    return context


