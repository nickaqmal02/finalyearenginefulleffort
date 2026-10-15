"""
Dashboard callback for unfold admin index page.
Computes all analytics data and passes to templates/admin/index.html.
"""
import json
from django.db.models import Count, Sum, Q, Avg
from .models import (
    User, Conversation, Topic, MessageTopic, DiagnosisDocument,
    ClientTopicScore, AutismDiagnosis,
)


def dashboard_callback(request, context):
    """
    Called by unfold before rendering admin/index.html.
    Enriches context with full analytics data.
    """
    # ── KPI counts ─────────────────────────────────
    context["total_clients"] = User.objects.filter(role="client", is_active=True).count()
    context["total_therapists"] = User.objects.filter(role="therapist", is_active=True).count()
    context["total_doctors"] = User.objects.filter(role="doctor", is_active=True).count()
    context["total_users"] = User.objects.count()
    context["total_conversations"] = Conversation.objects.count()
    context["total_topics"] = Topic.objects.filter(status="active").count()
    context["total_documents"] = DiagnosisDocument.objects.count()

    # ── Sentiment totals ──────────────────────────
    conversations = Conversation.objects.filter(sentiment__isnull=False)
    sentiment_totals = conversations.aggregate(
        positive=Count("id", filter=Q(sentiment="positive")),
        negative=Count("id", filter=Q(sentiment="negative")),
        neutral=Count("id", filter=Q(sentiment="neutral")),
    )
    avg_sentiment_score = conversations.aggregate(
        avg=Avg("sentiment_score")
    )["avg"] or 0
    context["avg_sentiment_score"] = round(avg_sentiment_score, 2)

    # Sentiment doughnut chart data
    context["sentiment_doughnut"] = json.dumps({
        "labels": ["Positive", "Negative", "Neutral"],
        "datasets": [{
            "data": [
                sentiment_totals["positive"],
                sentiment_totals["negative"],
                sentiment_totals["neutral"],
            ],
            "backgroundColor": ["#10b981", "#ef4444", "#9ca3af"],
            "borderWidth": 0,
            "hoverOffset": 8,
        }],
    })

    # ── Sentiment trend over time ────────────────
    progress = (
        Conversation.objects
        .filter(sentiment__isnull=False, date__isnull=False)
        .values("date")
        .annotate(score=Sum("sentiment_score"), count=Count("id"))
        .order_by("date")
    )
    context["sentiment_trend"] = json.dumps({
        "labels": [p["date"].strftime("%Y-%m-%d") for p in progress],
        "datasets": [{
            "label": "Daily Sentiment Score",
            "data": [round(p["score"], 2) for p in progress],
            "borderColor": "#6366f1",
            "backgroundColor": "rgba(99, 102, 241, 0.08)",
            "fill": True,
            "tension": 0.35,
            "pointBackgroundColor": "#6366f1",
            "pointRadius": 3,
            "pointHoverRadius": 6,
        }],
    })

    # ── Topic distribution ───────────────────────
    topics = Topic.objects.filter(status="active")
    topic_colors = ["#6366f1", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6",
                    "#06b6d4", "#ec4899", "#84cc16"]

    topic_distribution = []
    for i, t in enumerate(topics):
        scores = ClientTopicScore.objects.filter(topic=t)
        total_msgs = scores.aggregate(total=Sum("message_count"))["total"] or 0
        avg_score = scores.aggregate(avg=Avg("score"))["avg"] or 0
        client_count = scores.count()
        topic_distribution.append({
            "name": t.name,
            "total_msgs": total_msgs,
            "avg_score": round(avg_score, 2),
            "client_count": client_count,
            "color": topic_colors[i % len(topic_colors)],
        })
    topic_distribution.sort(key=lambda x: -x["total_msgs"])

    # Bar chart data (2D)
    context["topic_bar"] = json.dumps({
        "labels": [t["name"] for t in topic_distribution],
        "datasets": [{
            "label": "Message Count",
            "data": [t["total_msgs"] for t in topic_distribution],
            "backgroundColor": [t["color"] for t in topic_distribution],
            "borderRadius": 8,
            "borderWidth": 0,
        }],
    })

    # Radar chart (keep existing for backward compat)
    context["topic_radar"] = json.dumps({
        "labels": [t["name"] for t in topic_distribution],
        "datasets": [{
            "label": "Messages per Topic",
            "data": [t["total_msgs"] for t in topic_distribution],
            "backgroundColor": "rgba(99, 102, 241, 0.15)",
            "borderColor": "#6366f1",
            "pointBackgroundColor": "#6366f1",
            "borderWidth": 2,
        }],
    })

    context["topic_distribution"] = topic_distribution

    # ── Topic × Sentiment matrix ──────────────────
    topic_sentiment_matrix = []
    for i, t in enumerate(topics):
        convs = Conversation.objects.filter(
            topics__topic=t, sentiment__isnull=False
        ).distinct()
        pos = convs.filter(sentiment="positive").count()
        neu = convs.filter(sentiment="neutral").count()
        neg = convs.filter(sentiment="negative").count()
        total = pos + neu + neg
        topic_sentiment_matrix.append({
            "name": t.name,
            "positive": pos,
            "neutral": neu,
            "negative": neg,
            "total": total,
            "pos_pct": round(pos / total * 100, 1) if total else 0,
            "neg_pct": round(neg / total * 100, 1) if total else 0,
            "color": topic_colors[i % len(topic_colors)],
        })
    topic_sentiment_matrix.sort(key=lambda x: -x["total"])

    context["topic_sentiment_matrix"] = topic_sentiment_matrix

    # 3D Bubble chart: x=positive, y=negative, r=total/3
    context["topic_bubble"] = json.dumps({
        "datasets": [{
            "label": "Topics",
            "data": [
                {
                    "x": ts["positive"],
                    "y": ts["negative"],
                    "r": max(ts["total"] / 3, 8),
                    "topic_name": ts["name"],
                    "total": ts["total"],
                    "positive": ts["positive"],
                    "negative": ts["negative"],
                    "neutral": ts["neutral"],
                }
                for ts in topic_sentiment_matrix
            ],
            "backgroundColor": [
                topic_colors[i % len(topic_colors)]
                for i in range(len(topic_sentiment_matrix))
            ],
        }],
    })

    # 3D scatter data for ECharts GL (Obsidian-style floating topics)
    # X = positive count, Y = negative count, Z = total messages
    import math
    import random
    random.seed(42)

    # Force-directed-ish positions in 3D space (circular layout with jitter)
    num_topics = len(topic_sentiment_matrix)
    positions = []
    for i in range(num_topics):
        angle = (i / num_topics) * 2 * math.pi
        radius = 30 + random.uniform(-5, 5)
        positions.append({
            "x": radius * math.cos(angle) + random.uniform(-8, 8),
            "y": radius * math.sin(angle) + random.uniform(-8, 8),
            "z": random.uniform(-15, 15),
        })

    # Build nodes and links
    scatter_3d_points = []
    for i, ts in enumerate(topic_sentiment_matrix):
        pos = positions[i]
        scatter_3d_points.append({
            "value": [pos["x"], pos["y"], pos["z"]],
            "name": ts["name"],
            "color": ts["color"],
            "size": max(ts["total"] / 2, 30),
            "positive": ts["positive"],
            "negative": ts["negative"],
            "neutral": ts["neutral"],
            "total": ts["total"],
            "pos_pct": ts["pos_pct"],
            "neg_pct": ts["neg_pct"],
        })

    # Build links between similar topics
    scatter_3d_links = []
    for i in range(num_topics):
        for j in range(i + 1, num_topics):
            a = topic_sentiment_matrix[i]
            b = topic_sentiment_matrix[j]
            similarity = 1 - abs(a["pos_pct"] - b["pos_pct"]) / 100 - abs(a["neg_pct"] - b["neg_pct"]) / 100
            if similarity > 0.55:
                scatter_3d_links.append({
                    "source": [positions[i]["x"], positions[i]["y"], positions[i]["z"]],
                    "target": [positions[j]["x"], positions[j]["y"], positions[j]["z"]],
                    "similarity": round(similarity, 2),
                })

    # Build small message-dots around each topic center (Obsidian-style clusters)
    # Each dot represents a message belonging to that topic
    message_dots = []
    for i, ts in enumerate(topic_sentiment_matrix):
        pos = positions[i]
        # Number of dots scales with message count (capped for visual balance)
        num_dots = min(max(ts["total"] // 2, 6), 24)
        for _ in range(num_dots):
            # Gaussian scatter around the center
            dx = random.gauss(0, 8)
            dy = random.gauss(0, 8)
            dz = random.gauss(0, 6)
            message_dots.append({
                "value": [pos["x"] + dx, pos["y"] + dy, pos["z"] + dz],
                "color": ts["color"],
                "size": 3,
                "topic": ts["name"],
            })

    context["topic_3d_scatter"] = json.dumps({
        "points": scatter_3d_points,
        "links": scatter_3d_links,
        "message_dots": message_dots,
    })

    # Cohort data for unfold component (keep existing)
    cohort_data = {
        "headers": [
            {"title": "Positive", "subtitle": "😊"},
            {"title": "Negative", "subtitle": "😕"},
            {"title": "Neutral", "subtitle": "😑"},
            {"title": "Total", "subtitle": " "},
        ],
        "rows": [],
    }
    for ts in topic_sentiment_matrix:
        cohort_data["rows"].append({
            "header": {
                "title": ts["name"],
                "subtitle": f"{ts['total']} messages",
            },
            "cols": [
                {"value": str(ts["positive"]), "color": "bg-green-100 border border-green-300 rounded-xl"},
                {"value": str(ts["negative"]), "color": "bg-red-100 border border-red-300 rounded-xl"},
                {"value": str(ts["neutral"]), "color": "bg-gray-100 border border-gray-300 rounded-xl"},
                {"value": str(ts["total"]), "color": "bg-blue-50 border border-blue-200 rounded-xl"},
            ],
        })
    context["topic_sentiment_data"] = cohort_data

    # ── Diagnosis distribution ────────────────────
    diagnosis_levels = []
    for level, label, color in [
        (1, "Level 1 - Requiring Support", "#10b981"),
        (2, "Level 2 - Requiring Substantial Support", "#f59e0b"),
        (3, "Level 3 - Requiring Very Substantial Support", "#ef4444"),
    ]:
        count = AutismDiagnosis.objects.filter(support_level=level, is_active=True).count()
        diagnosis_levels.append({"level": level, "label": label, "count": count, "color": color})

    context["diagnosis_levels"] = diagnosis_levels
    context["diagnosis_doughnut"] = json.dumps({
        "labels": [d["label"] for d in diagnosis_levels],
        "datasets": [{
            "data": [d["count"] for d in diagnosis_levels],
            "backgroundColor": [d["color"] for d in diagnosis_levels],
            "borderWidth": 0,
        }],
    })

    # ── Therapist workload ───────────────────────
    therapists = User.objects.filter(role="therapist", is_active=True)
    therapist_workload = []
    for t in therapists:
        client_count = User.objects.filter(role="client", assigned_therapist=t).count()
        conv_count = Conversation.objects.filter(therapist=t).count()
        therapist_workload.append({
            "name": t.get_full_name(),
            "client_count": client_count,
            "conv_count": conv_count,
        })
    therapist_workload.sort(key=lambda x: -x["conv_count"])

    context["therapist_workload"] = therapist_workload
    context["therapist_bar"] = json.dumps({
        "labels": [t["name"] for t in therapist_workload],
        "datasets": [{
            "label": "Conversations",
            "data": [t["conv_count"] for t in therapist_workload],
            "backgroundColor": "#6366f1",
            "borderRadius": 8,
        }, {
            "label": "Assigned Clients",
            "data": [t["client_count"] for t in therapist_workload],
            "backgroundColor": "#10b981",
            "borderRadius": 8,
        }],
    })

    return context
