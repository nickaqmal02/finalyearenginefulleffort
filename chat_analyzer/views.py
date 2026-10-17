from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden, JsonResponse
from django.utils import timezone
from typing import Any
from django.db.models import QuerySet
from django.contrib import messages
from datetime import datetime
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie, csrf_exempt
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomLoginForm, CustomSignUpForm, UploadChatForm, UploadDocumentForm
from .models import User, ChatThread, ChatMessage
from .decorators import admin_required, therapist_required, doctor_required, client_required
# ████████████████████████████████████████████████████████████████████████████████
# █░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█
# █░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░
# █░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█
# █                         🧠 VIEWS NICKY PORJECT 🧠                                █
# █        BY NICKY 02 : START FOR THERAPIST SECTION 3 AUG 2026 0052H 
# █                      Sentiment Analysis Integration                           █
# █░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█░░░█
# █░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░░█░
# █░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█░█
# ████████████████████████████████████████████████████████████████████████████████
#
#========================
# 1. WELCOMING PAGE VIEWS 😊
# =======================
def welcome_view(request):
    return render(request, 'chat_analyzer/welcome.html')

# ================================
# 2. AUTHENTICATION SECTION VIEWS 🔑
# ================================
@ensure_csrf_cookie
@csrf_protect
def login_view(request):
    """ for better customization in future """
    
    # for if user already logged in
    if request.user.is_authenticated:
        messages.success(request, f"Welcome back !")
        if request.user.is_admin:
            return redirect('chat_analyzer:admin_dashboard')

        elif request.user.is_therapist:
            return redirect('chat_analyzer:therapist_dashboard')

        elif request.user.is_doctor:
            return redirect('chat_analyzer:doctor_dashboard')
            
        elif request.user.is_client:
            return redirect('chat_analyzer:client_dashboard')

        else:
            return redirect('chat_analyzer:welcome_view')

    # than if method post
    if request.method == "POST":

        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                # then redirect to dashboard
                if user.is_admin:
                    return redirect('chat_analyzer:admin_dashboard')

                elif user.is_therapist:
                    return redirect('chat_analyzer:therapist_dashboard')

                elif user.is_doctor:
                    return redirect('chat_analyzer:doctor_dashboard')
            
                elif user.is_client:
                    return redirect('chat_analyzer:client_dashboard')

                else:
                    return redirect('chat_analyzer:welcome_view')
            else:
                messages.error(request, "invalid username or password")
        else:
            messages.error(request, "invalid username or password")
    else:
        # we display back our custom login form
        form = CustomLoginForm()

    return render(request, 'chat_analyzer/auth/login.html', {'form': form})
#· · · · · · · · · · · · · · · · · · · · · · 
#  2.2 LOGOUT VIEWS                          
#· · · · · · · · · · · · · · · · · · · · · · 
@csrf_protect
def logout_view(request):
    """logout views section"""
    logout(request)
    request.session.flush()
    messages.info(request, "You have been logged out successfully")
    return redirect('chat_analyzer:login_view')


#· · · · · · · · · · · · · · · · · · · · · · 
#  2.3 SIGNUP VIEWS                          
#· · · · · · · · · · · · · · · · · · · · · · 
@ensure_csrf_cookie
@csrf_protect
def signup_view(request):
    """Custom Signup Form"""
    # first skali always check wether they already login or not
    if request.user.is_authenticated:
        if request.user.is_admin:
            return redirect('chat_analyzer:admin_dashboard')
        elif request.user.is_therapist:
            return redirect('chat_analyzer:therapist_dashboard')
        elif request.user.is_doctor:
            return redirect('chat_analyzer:doctor_dashboard')
        elif request.user.is_client:
            return redirect('chat_analyzer:client_dashboard')
        else:
            return redirect('chat_analyzer:welcome_view')

    # then if request POST we must handle it
    if request.method == "POST":
        form = CustomSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()

            # log the user directly after the login
            login(request, user)
            messages.success(request, f"Account created successfully ! Welcome, {user.username} !")
            
            # redirect based on role
            if user.is_admin:
                return redirect('chat_analyzer:admin_dashboard')
            elif user.is_therapist:
                return redirect('chat_analyzer:therapist_dashboard')
            elif user.is_doctor:
                return redirect('chat_analyzer:doctor_dashboard')
            elif user.is_client:
                return redirect('chat_analyzer:client_dashboard')
            else:
                return redirect('chat_analyzer:welcome_view')
        
        else:
            # display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomSignUpForm()

    return render(request, 'chat_analyzer/auth/signup.html', {'form': form})
        

# ===========================
# 3. DASHBOARD FOR EACH ROLE 🔒 using decorators
# ===========================
#
@admin_required
def admin_dashboard(request):
    """Admin analytics dashboard: clinic-wide overview with rich visualizations."""
    from django.db.models import Count, Sum, Q, Avg
    from .models import Conversation, Topic, ClientTopicScore, AutismDiagnosis
    import json

    # ── KPI cards ──────────────────────────────────
    total_users = User.objects.count()
    total_therapists = User.objects.filter(role='therapist', is_active=True).count()
    total_clients = User.objects.filter(role='client', is_active=True).count()
    total_doctors = User.objects.filter(role='doctor', is_active=True).count()

    # ── Conversations & Sentiment ─────────────────
    conversations = Conversation.objects.filter(sentiment__isnull=False)
    total_conversations = conversations.count()

    sentiment_totals = conversations.aggregate(
        positive=Count('id', filter=Q(sentiment='positive')),
        negative=Count('id', filter=Q(sentiment='negative')),
        neutral=Count('id', filter=Q(sentiment='neutral')),
    )
    avg_sentiment_score = conversations.aggregate(
        avg=Avg('sentiment_score')
    )['avg'] or 0

    # ── Sentiment trend over time ─────────────────
    progress = (
        Conversation.objects
        .filter(sentiment__isnull=False, date__isnull=False)
        .values('date')
        .annotate(score=Sum('sentiment_score'), count=Count('id'))
        .order_by('date')
    )
    trend_data = json.dumps({
        "labels": [p['date'].strftime('%Y-%m-%d') for p in progress],
        "datasets": [{
            "label": "Daily Sentiment Score",
            "data": [round(p['score'], 2) for p in progress],
            "borderColor": "#6366f1",
            "backgroundColor": "rgba(99, 102, 241, 0.08)",
            "fill": True,
            "tension": 0.35,
            "pointBackgroundColor": "#6366f1",
            "pointRadius": 3,
            "pointHoverRadius": 6,
        }],
    })

    # ── Topic distribution ─────────────────────────
    topics = Topic.objects.filter(status='active')
    topic_distribution = []
    topic_colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
                    '#06b6d4', '#ec4899', '#84cc16']

    for i, t in enumerate(topics):
        scores = ClientTopicScore.objects.filter(topic=t)
        total_msgs = scores.aggregate(total=Sum('message_count'))['total'] or 0
        avg_score = scores.aggregate(avg=Avg('score'))['avg'] or 0
        client_count = scores.count()
        topic_distribution.append({
            'name': t.name,
            'total_msgs': total_msgs,
            'avg_score': round(avg_score, 2),
            'client_count': client_count,
            'color': topic_colors[i % len(topic_colors)],
        })
    topic_distribution.sort(key=lambda x: -x['total_msgs'])

    # Chart.js data for topic distribution (2D bar chart)
    topic_chart_data = json.dumps({
        "labels": [t['name'] for t in topic_distribution],
        "datasets": [{
            "label": "Message Count",
            "data": [t['total_msgs'] for t in topic_distribution],
            "backgroundColor": [t['color'] for t in topic_distribution],
            "borderRadius": 8,
            "borderWidth": 0,
        }],
    })

    # ── Topic × Sentiment matrix (for 3D/bubble chart) ──
    topic_sentiment_matrix = []
    for t in topics:
        convs = Conversation.objects.filter(
            topics__topic=t, sentiment__isnull=False
        ).distinct()
        pos = convs.filter(sentiment='positive').count()
        neu = convs.filter(sentiment='neutral').count()
        neg = convs.filter(sentiment='negative').count()
        total = pos + neu + neg
        topic_sentiment_matrix.append({
            'name': t.name,
            'positive': pos,
            'neutral': neu,
            'negative': neg,
            'total': total,
            'pos_pct': round(pos / total * 100, 1) if total else 0,
            'neg_pct': round(neg / total * 100, 1) if total else 0,
        })
    topic_sentiment_matrix.sort(key=lambda x: -x['total'])

    # 3D bubble chart data: x=positive, y=negative, z/size=total
    bubble_data = json.dumps({
        "datasets": [{
            "label": "Topics",
            "data": [
                {
                    "x": ts['positive'],
                    "y": ts['negative'],
                    "r": max(ts['total'] / 3, 8),
                    "topic_name": ts['name'],
                    "total": ts['total'],
                    "positive": ts['positive'],
                    "negative": ts['negative'],
                    "neutral": ts['neutral'],
                }
                for ts in topic_sentiment_matrix
            ],
            "backgroundColor": [
                topic_colors[i % len(topic_colors)]
                for i in range(len(topic_sentiment_matrix))
            ],
        }],
    })

    # ── Diagnosis distribution ────────────────────
    diagnosis_levels = []
    for level, label in [(1, 'Level 1 - Requiring Support'),
                         (2, 'Level 2 - Requiring Substantial Support'),
                         (3, 'Level 3 - Requiring Very Substantial Support')]:
        count = AutismDiagnosis.objects.filter(support_level=level, is_active=True).count()
        diagnosis_levels.append({'level': level, 'label': label, 'count': count})

    diagnosis_chart_data = json.dumps({
        "labels": [d['label'] for d in diagnosis_levels],
        "datasets": [{
            "data": [d['count'] for d in diagnosis_levels],
            "backgroundColor": ['#10b981', '#f59e0b', '#ef4444'],
            "borderWidth": 0,
        }],
    })

    # ── Therapist workload ─────────────────────────
    therapists = User.objects.filter(role='therapist', is_active=True)
    therapist_workload = []
    for t in therapists:
        client_count = User.objects.filter(role='client', assigned_therapist=t).count()
        conv_count = Conversation.objects.filter(therapist=t).count()
        therapist_workload.append({
            'name': t.get_full_name(),
            'client_count': client_count,
            'conv_count': conv_count,
        })
    therapist_workload.sort(key=lambda x: -x['conv_count'])

    therapist_chart_data = json.dumps({
        "labels": [t['name'] for t in therapist_workload],
        "datasets": [{
            "label": "Conversations",
            "data": [t['conv_count'] for t in therapist_workload],
            "backgroundColor": "#6366f1",
            "borderRadius": 8,
        }, {
            "label": "Assigned Clients",
            "data": [t['client_count'] for t in therapist_workload],
            "backgroundColor": "#10b981",
            "borderRadius": 8,
        }],
    })

    context = {
        # KPIs
        'total_users': total_users,
        'total_therapists': total_therapists,
        'total_clients': total_clients,
        'total_doctors': total_doctors,
        'total_conversations': total_conversations,
        'avg_sentiment_score': round(avg_sentiment_score, 2),
        # Sentiment
        'sentiment_totals': sentiment_totals,
        'trend_data': trend_data,
        # Topics
        'topic_distribution': topic_distribution,
        'topic_chart_data': topic_chart_data,
        'topic_sentiment_matrix': topic_sentiment_matrix,
        'bubble_data': bubble_data,
        # Diagnoses
        'diagnosis_levels': diagnosis_levels,
        'diagnosis_chart_data': diagnosis_chart_data,
        # Therapists
        'therapist_workload': therapist_workload,
        'therapist_chart_data': therapist_chart_data,
    }
    return render(request, 'chat_analyzer/admin/admin_dashboard.html', context)

@therapist_required
def therapist_dashboard(request):
    """Therapist dashboard: assigned clients + their sentiment/progress overview."""
    from .models import Conversation, AutismDiagnosis, ClientTopicScore
    from django.db.models import Count, Sum, Q, Avg
    import json

    therapist = request.user
    clients = therapist.assigned_clients.filter(is_active=True)

    # Per-client analytics
    client_data = []
    for client in clients:
        convs = Conversation.objects.filter(client=client, sentiment__isnull=False)
        sentiment = convs.aggregate(
            positive=Count('id', filter=Q(sentiment='positive')),
            negative=Count('id', filter=Q(sentiment='negative')),
            neutral=Count('id', filter=Q(sentiment='neutral')),
        )
        total = convs.count()
        diagnosis = AutismDiagnosis.objects.filter(
            client=client, is_active=True
        ).first()
        client_data.append({
            'client': client,
            'total_messages': total,
            'positive': sentiment['positive'],
            'negative': sentiment['negative'],
            'neutral': sentiment['neutral'],
            'positive_pct': round(sentiment['positive'] / total * 100) if total else 0,
            'negative_pct': round(sentiment['negative'] / total * 100) if total else 0,
            'support_level': diagnosis.support_level if diagnosis else None,
            'last_message': convs.order_by('-date', '-time').first(),
        })

    # Aggregate stats
    all_convs = Conversation.objects.filter(
        client__assigned_therapist=therapist, sentiment__isnull=False
    )
    total_messages = all_convs.count()
    total_positive = all_convs.filter(sentiment='positive').count()
    avg_sentiment = all_convs.aggregate(avg=Avg('sentiment_score'))['avg'] or 0

    # Recent chat threads (top 5 by last_message_at) — for dashboard widget
    from .models import ChatThread, ChatMessage
    recent_chats = ChatThread.objects.filter(
        therapist=therapist
    ).select_related('client').order_by('-last_message_at')[:5]

    # Pre-compute last-message preview for each thread
    recent_chats_data = []
    for t in recent_chats:
        last_msg = t.messages.order_by('-sent_at').first()
        recent_chats_data.append({
            'thread': t,
            'last_message': last_msg.message if last_msg else 'No messages yet',
            'unread': t.therapist_unread,
        })

    # ── ANALYZED MESSAGES WIDGET ──
    # Recent Conversation rows (from live chat + WhatsApp) with sentiment + topic
    # These are the ML-analyzed messages — shows the therapist what the pipeline found
    # Sort by message date (when the message was actually sent), NOT created_at (when it was imported)
    from .models import MessageTopic
    recent_analyzed = Conversation.objects.filter(
        client__assigned_therapist=therapist,
        sentiment__isnull=False,
        is_from_client=True,  # only client messages have topics
    ).select_related('client').order_by('-date', '-time')[:8]

    recent_analyzed_data = []
    for conv in recent_analyzed:
        # Get the primary topic for this message (if any)
        primary_mt = MessageTopic.objects.filter(
            conversation=conv, is_primary=True
        ).select_related('topic').first()
        # Fallback: any topic match if no primary
        topic_entry = primary_mt or MessageTopic.objects.filter(
            conversation=conv
        ).select_related('topic').first()

        recent_analyzed_data.append({
            'conv': conv,
            'topic': topic_entry.topic if topic_entry else None,
            'topic_score': topic_entry.score if topic_entry else None,
        })

    context = {
        'therapist': therapist,
        'clients': client_data,
        'total_clients': clients.count(),
        'total_messages': total_messages,
        'total_positive': total_positive,
        'avg_sentiment': round(avg_sentiment, 2),
        'recent_chats': recent_chats_data,
        'recent_analyzed': recent_analyzed_data,
    }
    return render(request, 'chat_analyzer/MainTherapist/dashboard.html', context)


@therapist_required
def therapist_upload_chat(request):
    """Therapist uploads WhatsApp .txt for their assigned clients."""
    from .models import User
    from .forms import TherapistUploadChatForm
    from chat_analyzer.services.upload_service import process_whatsapp_upload

    therapist = request.user

    if request.method == 'POST':
        form = TherapistUploadChatForm(request.POST, request.FILES, therapist=therapist)
        if form.is_valid():
            result = process_whatsapp_upload(
                file_path_or_file=request.FILES['chat_file'],
                client_id=form.cleaned_data['client'].id,
                uploader_id=therapist.id,
                chat_type='individual',  # therapist chats are always 1-on-1
                therapist_id=therapist.id,
            )
            if 'error' in result:
                messages.error(request, f"❌ {result['error']}")
            else:
                from chat_analyzer.services.topic_modeler import train_topics
                try:
                    train_topics()
                except Exception as e:
                    messages.warning(request, f"⚠️ Topic training failed: {e}")
                messages.success(
                    request,
                    f"✅ Saved {result['saved']} messages ({result['positive']} pos / "
                    f"{result['negative']} neg / {result['neutral']} neu) — topics retrained",
                )
            return redirect('chat_analyzer:therapist_dashboard')
    else:
        form = TherapistUploadChatForm(therapist=therapist)

    return render(request, 'chat_analyzer/MainTherapist/upload_chat.html', {
        'form': form,
        'therapist': therapist,
    })


@therapist_required
def therapist_client_detail(request, client_id):
    """Therapist view of a single client's full progress."""
    from .models import User, Conversation, AutismDiagnosis, ClientSpecifier, ClientTopicScore
    from django.db.models import Count, Sum, Q
    import json

    therapist = request.user
    client = get_object_or_404(
        User, id=client_id, role='client', assigned_therapist=therapist
    )

    convs = Conversation.objects.filter(client=client, sentiment__isnull=False)
    sentiment = convs.aggregate(
        positive=Count('id', filter=Q(sentiment='positive')),
        negative=Count('id', filter=Q(sentiment='negative')),
        neutral=Count('id', filter=Q(sentiment='neutral')),
    )
    total = convs.count()

    # Progress over time
    progress = (
        convs.filter(date__isnull=False)
        .values('date')
        .annotate(score=Sum('sentiment_score'))
        .order_by('date')
    )
    chart_data = json.dumps({
        "labels": [p['date'].strftime('%Y-%m-%d') for p in progress],
        "datasets": [{
            "label": "Sentiment",
            "data": [round(p['score'], 2) for p in progress],
            "borderColor": "#0071e3",
            "backgroundColor": "rgba(0, 113, 227, 0.12)",
            "fill": True,
            "tension": 0.35,
            "pointRadius": 3,
            "borderWidth": 2,
        }],
    })

    # Topics
    topics = ClientTopicScore.objects.filter(
        client=client, topic__status='active'
    ).select_related('topic').order_by('-message_count')

    # Diagnosis + specifiers
    diagnosis = AutismDiagnosis.objects.filter(client=client, is_active=True).first()
    specifiers = ClientSpecifier.objects.filter(
        autism_diagnosis=diagnosis
    ).select_related('specifier') if diagnosis else []

    # Recent messages
    recent = Conversation.objects.filter(client=client).order_by('-date', '-time')[:10]

    context = {
        'client': client,
        'sentiment': sentiment,
        'total': total,
        'chart_data': chart_data,
        'topics': topics,
        'diagnosis': diagnosis,
        'specifiers': specifiers,
        'recent': recent,
        'positive_pct': round(sentiment['positive'] / total * 100) if total else 0,
        'negative_pct': round(sentiment['negative'] / total * 100) if total else 0,
    }
    return render(request, 'chat_analyzer/MainTherapist/ClientTherapist/client_detail.html', context)

@therapist_required
def therapist_chat_threads(request):
    threads = ChatThread.objects.filter(
        therapist=request.user
    ).select_related('client').order_by('-last_message_at')

    # Pre-compute last-message preview + sender (for the inbox)
    threads_data = []
    for t in threads:
        last_msg = t.messages.order_by('-sent_at').first()
        threads_data.append({
            'thread': t,
            'last_message': last_msg.message if last_msg else None,
            'last_message_sender': last_msg.sender.get_full_name() if last_msg else None,
            'last_message_is_mine': last_msg.sender_id == request.user.id if last_msg else False,
            'last_message_at': t.last_message_at,
            'unread': t.therapist_unread,
        })

    context = {
        'therapist': request.user,
        'threads': threads_data,
    }
    return render(request, 'chat_analyzer/MainTherapist/chat_threads.html', context)


@login_required
def doctor_chat_threads(request):
    """Doctor's chat inbox — all threads where doctor is a participant."""
    if request.user.role != 'doctor':
        return HttpResponseForbidden("Doctors only.")

    threads = ChatThread.objects.filter(
        doctor=request.user
    ).select_related('client').order_by('-last_message_at')

    threads_data = []
    for t in threads:
        last_msg = t.messages.order_by('-sent_at').first()
        threads_data.append({
            'thread': t,
            'last_message': last_msg.message if last_msg else 'No messages yet',
            'last_message_sender': last_msg.sender.get_full_name() if last_msg else None,
            'last_message_is_mine': last_msg.sender_id == request.user.id if last_msg else False,
            'last_message_at': t.last_message_at,
            'unread': t.doctor_unread,
        })

    context = {
        'doctor': request.user,
        'threads': threads_data,
    }
    return render(request, 'chat_analyzer/MainTherapist/chat_threads.html', context)

@login_required
def chat_thread_detail(request, thread_id):
    """Live chat thread detail — works for client, therapist, AND doctor."""
    thread = get_object_or_404(ChatThread, id=thread_id)

    # SECURITY: only the people in this thread can view it
    if request.user != thread.client and request.user != thread.therapist and request.user != thread.doctor:
        return HttpResponseForbidden("You are not part of this thread.")

    # Handle "send message" POST
    if request.method == 'POST':
        text = request.POST.get('message', '').strip()
        if text:
            ChatMessage.objects.create(
                thread=thread,
                sender=request.user,
                message=text,
            )
            # Update unread counter (the OTHER person)
            thread.last_message_at = timezone.now()
            if request.user == thread.client:
                if thread.therapist:
                    thread.therapist_unread += 1
                if thread.doctor:
                    thread.doctor_unread += 1
            elif request.user == thread.therapist:
                thread.client_unread += 1
                if thread.doctor:
                    thread.doctor_unread += 1
            elif request.user == thread.doctor:
                thread.client_unread += 1
                if thread.therapist:
                    thread.therapist_unread += 1
            thread.save()

            # ── BRIDGE: live chat → ML pipeline ──
            # Create a Conversation row so the SAME pipeline that processes
            # WhatsApp uploads can also process live chat messages.
            # Sentiment/topic stay None until the Celery task fires (5-min delay).
            from .models import Conversation
            from .tasks import analyze_live_message
            import hashlib

            is_client = request.user == thread.client
            msg_hash = hashlib.sha256(
                f"live-{thread.id}-{request.user.id}-{timezone.now().isoformat()}".encode()
            ).hexdigest()

            conv = Conversation.objects.create(
                client=thread.client,
                therapist=thread.therapist if not is_client else None,
                sender=request.user,
                is_from_client=is_client,
                date=timezone.now().date(),
                time=timezone.now().time(),
                username=request.user.get_full_name() or request.user.username,
                message=text,
                chat_type='individual',
                message_hash=msg_hash,
                is_processed=False,
            )

            # Fire the Celery task — 5-minute delay so it doesn't
            # interfere with the active conversation
            analyze_live_message.apply_async(
                args=[conv.id],
                countdown=300,  # 5 minutes
            )

            return redirect('chat_analyzer:chat_thread_detail', thread_id=thread.id)

    # Mark messages from the OTHER person as read
    ChatMessage.objects.filter(
        thread=thread,
        is_read=False,
    ).exclude(sender=request.user).update(is_read=True, read_at=timezone.now())

    # Reset MY unread counter
    if request.user == thread.client:
        thread.client_unread = 0
    elif request.user == thread.therapist:
        thread.therapist_unread = 0
    elif request.user == thread.doctor:
        thread.doctor_unread = 0
    thread.save()

    # Redirect: client → client template, doctor → therapist template, therapist → therapist template
    messages = thread.messages.select_related('sender').order_by('sent_at')

    if request.user.role == 'client':
        template = 'chat_analyzer/client/chat_thread.html'
    else:
        template = 'chat_analyzer/MainTherapist/chat_thread.html'

    context = {
        'thread': thread,
        'messages': messages,
        'me': request.user,
        'other': thread.therapist if request.user == thread.client else thread.client,
    }
    return render(request, template, context)


@login_required
def client_messages(request):
    """Client-side chat history list — mirrors therapist inbox but scoped to the client."""
    if request.user.role != 'client':
        return HttpResponseForbidden('Clients only.')

    from .models import ChatThread
    threads = ChatThread.objects.filter(
        client=request.user
    ).select_related('therapist').order_by('-last_message_at')

    threads_data = []
    for t in threads:
        last_msg = t.messages.order_by('-sent_at').first()
        threads_data.append({
            'thread': t,
            'last_message': last_msg.message if last_msg else 'No messages yet',
            'last_message_sender': last_msg.sender.get_full_name() if last_msg else None,
            'last_message_is_mine': last_msg.sender_id == request.user.id if last_msg else False,
            'last_message_at': t.last_message_at,
            'unread': t.client_unread,
        })

    context = {
        'client_user': request.user,
        'threads': threads_data,
        'unread_client_messages_count': sum(t['unread'] for t in threads_data),
    }
    return render(request, 'chat_analyzer/client/messages.html', context)


@login_required
def start_chat_with_therapist(request):
    """Client-side: find-or-create the thread between me (the client) and my assigned therapist, redirect in."""
    from .models import User, ChatThread
    client = request.user
    if client.role != 'client' or not client.assigned_therapist:
        return HttpResponseForbidden('No assigned therapist.')
    thread, _ = ChatThread.objects.get_or_create(
        client=client,
        therapist=client.assigned_therapist,
    )
    return redirect('chat_analyzer:client_chat_thread', thread_id=thread.id)


@therapist_required
def start_chat_with_client(request, client_id):
    """Auto-create the thread (one per client-therapist pair) and redirect to it."""
    from .models import User
    client = get_object_or_404(User, id=client_id, role='client')

    # Security: only the assigned therapist
    if client.assigned_therapist != request.user:
        return HttpResponseForbidden('This client is not assigned to you.')

    thread, created = ChatThread.objects.get_or_create(
        client=client,
        therapist=request.user,
    )
    return redirect('chat_analyzer:chat_thread_detail', thread_id=thread.id)




@doctor_required
def doctor_dashboard(request):
    """Doctor dashboard: pending document approvals + diagnosed clients."""
    from .models import DiagnosisDocument, AutismDiagnosis, ClientSpecifier
    from django.db.models import Count, Q

    doctor = request.user

    # Pending documents (not yet approved)
    pending_docs = DiagnosisDocument.objects.filter(
        is_approved=False, is_active=True
    ).select_related('client', 'uploaded_by').order_by('upload_date')

    # Approved documents (this doctor approved)
    approved_docs = DiagnosisDocument.objects.filter(
        is_approved=True, approved_by=doctor
    ).select_related('client').order_by('-approval_date')

    # Diagnosed clients (diagnoses this doctor made)
    diagnoses = AutismDiagnosis.objects.filter(
        diagnosed_by=doctor, is_active=True
    ).select_related('client').order_by('-diagnosis_date')

    # Enrich each diagnosis with specifiers + message stats + chart data
    diagnosis_cards = []
    for diag in diagnoses:
        specifiers = ClientSpecifier.objects.filter(
            autism_diagnosis=diag, is_present=True
        ).select_related('specifier')[:5]

        from chat_analyzer.models import Conversation, MessageTopic, Topic
        import json as _json

        convs = Conversation.objects.filter(
            client=diag.client, sentiment__isnull=False, is_from_client=True
        ).order_by('date', 'time')
        msg_count = convs.count()

        # Sentiment distribution for mini doughnut
        sentiment_data = convs.aggregate(
            positive=Count('id', filter=Q(sentiment='positive')),
            negative=Count('id', filter=Q(sentiment='negative')),
            neutral=Count('id', filter=Q(sentiment='neutral')),
        )

        # Topic distribution for mini bars
        topics = MessageTopic.objects.filter(
            conversation__client=diag.client,
            is_primary=True,
        ).select_related('topic')
        topic_counts = {}
        for mt in topics:
            name = mt.topic.name
            if name not in topic_counts:
                topic_counts[name] = 0
            topic_counts[name] += 1
        topic_data = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Last 7 messages for trend line
        recent_msgs = convs.order_by('-date', '-time')[:7][::-1]
        trend_data = [[i, msg.sentiment_score or 0] for i, msg in enumerate(recent_msgs)]

        diagnosis_cards.append({
            'diag': diag,
            'specifiers': specifiers,
            'message_count': msg_count,
            'sentiment_data': sentiment_data,
            'topic_data': topic_data,
            'trend_data': _json.dumps(trend_data),
            'sentiment_json': _json.dumps([
                sentiment_data['positive'],
                sentiment_data['negative'],
                sentiment_data['neutral'],
            ]),
        })

    context = {
        'doctor': doctor,
        'pending_docs': pending_docs,
        'pending_count': pending_docs.count(),
        'approved_docs': approved_docs,
        'approved_count': approved_docs.count(),
        'diagnosis_cards': diagnosis_cards,
        'diagnosis_count': diagnoses.count(),
    }
    return render(request, 'chat_analyzer/doctor/doctor_dashboard.html', context)


@doctor_required
def doctor_approve_document(request, doc_id):
    """Doctor approves an autism diagnosis document."""
    from .models import DiagnosisDocument
    from django.utils import timezone

    doc = get_object_or_404(DiagnosisDocument, id=doc_id, is_active=True)

    if request.method == 'POST':
        doc.is_approved = True
        doc.approved_by = request.user
        doc.approval_date = timezone.now()
        doc.save()
        messages.success(
            request,
            f"✅ Approved document for {doc.client.get_full_name()} — {doc.get_document_type_display()}",
        )
        return redirect('chat_analyzer:doctor_dashboard')

    return render(request, 'chat_analyzer/doctor/approve_document.html', {
        'doc': doc,
        'doctor': request.user,
    })


@client_required
def client_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Displays the dashboard for a specific client.
    Shows their info and recent conversation topics.
    """
    from .models import AutismDiagnosis, ClientSpecifier, DiagnosisDocument, Conversation, ClientTopicScore, User
    from django.db.models import Count, Sum, Q, Avg
    import json
    
    # 1.fetch the the client from db
    client: User = request.user

    # 2. diagnosis
    diagnoses: QuerySet[AutismDiagnosis] = AutismDiagnosis.objects.filter(
        client=client
    ).order_by('diagnosis_date')

    specifiers: QuerySet[ClientSpecifier] = ClientSpecifier.objects.filter(
        autism_diagnosis__client=client,
        autism_diagnosis__is_active=True
    ).select_related('specifier')[:5]
    # 3. diagnosis docuemnts
    documents: QuerySet[DiagnosisDocument] = DiagnosisDocument.objects.filter(
        client=client
    ).order_by('-upload_date')

    # 4. sentiment totals
    convs: QuerySet[Conversation] = Conversation.objects.filter(client=client, sentiment__isnull=False)

    sentiment_totals: dict[str, int] = convs.aggregate(
        positive=Count('id', filter=Q(sentiment='positive')),
        negative=Count('id', filter=Q(sentiment='negative')),
        neutral=Count('id', filter=Q(sentiment='neutral')),
    )
    total_messages: int = convs.count()

    # 5. Topic breakdown
    topic_scores: QuerySet[ClientTopicScore] = ClientTopicScore.objects.filter(
        client=client,
        topic__status='active',
    ).select_related('topic').order_by('-message_count')[:5]

    # 6 progress chart data
    progress: QuerySet[dict] = (
        Conversation.objects
        .filter(client=client, sentiment__isnull=False, date__isnull=False)
        .values('date')
        .annotate(score=Sum('sentiment_score'), count=Count('id'))
        .order_by('date')
    )
    # then why ? this progress is dict ? because ...
    """
        we return the QuerySet of 
        [   
            {'date': datetime(2024, 1, 1), 'score':15},

        ]
        # we use .annotate() if we want to send Sum, Avg, Count, Max
        but may we actually declaring 4 key ?? yes ..

        progress: QuerySet[dict] = (
            Conversation.objects
            .filter(client=client, sentiment__isnull=False, date__isnull=False)
            .values('date','channel') -> this represent 2 keys
            .annotate(
                total_scores=Sum('sentiment_score'),
                message_count=Count('id')
            ) -> we use annotate to store some match calculation result if not we just stack it at values
            .order_by('date')
        )
    """
    # we use strftime to ensure that our date got pass into beautifull format "2024-01-15"
    date_strings: list[str] = [p['date'].strftime('%Y-%m-%d') for p in progress]
    scores: list[int] = [p['score'] for p in progress]
    counts: list[int] = [p['count'] for p in progress]

    chart_data: str = json.dumps({
        "labels": date_strings,
        "datasets": [
            {
                "label": "Sentiment Score",
                "data": scores,
                "borderColor": "#10b981",
                "backgroundColor": "rgba(16, 185, 129, 0.12)",
                "fill": True,
                "tension": 0.35,
                "pointBackgroundColor": "#10b981",
                "pointBorderColor": "#fff",
                "pointBorderWidth": 2,
                "pointRadius": 4,
                "pointHoverRadius": 7,
                "yAxisID": "y",
            },
            {
                "label": "Messages",
                "data": counts,
                "type": "bar",
                "backgroundColor": "rgba(99, 102, 241, 0.25)",
                "borderRadius": 4,
                "yAxisID": "y1",
                "order": 2,
            },
        ],
    })

    # ── Sentiment percentages ──────────────────────
    total_msgs = sentiment_totals['positive'] + sentiment_totals['negative'] + sentiment_totals['neutral']
    sentiment_pct = {
        'positive': round(sentiment_totals['positive'] / total_msgs * 100) if total_msgs else 0,
        'negative': round(sentiment_totals['negative'] / total_msgs * 100) if total_msgs else 0,
        'neutral': round(sentiment_totals['neutral'] / total_msgs * 100) if total_msgs else 0,
    }

    # ── Sentiment doughnut data (with percentages) ──
    sentiment_doughnut: str = json.dumps({
        "labels": ["Positive", "Negative", "Neutral"],
        "datasets": [{
            "data": [
                sentiment_totals['positive'],
                sentiment_totals['negative'],
                sentiment_totals['neutral'],
            ],
            "backgroundColor": ["#10b981", "#ef4444", "#9ca3af"],
            "borderWidth": 0,
            "hoverOffset": 10,
        }],
    })

    # ── Topic radar chart data ──────────────────────
    topic_radar: str = json.dumps({
        "labels": [ts.topic.name for ts in topic_scores],
        "datasets": [{
            "label": "Message Count",
            "data": [ts.message_count for ts in topic_scores],
            "backgroundColor": "rgba(139, 92, 246, 0.15)",
            "borderColor": "#8b5cf6",
            "pointBackgroundColor": "#8b5cf6",
            "borderWidth": 2,
            "pointRadius": 4,
        }],
    })

    # ── Latest session / most recent activity ──────
    latest_conversation = Conversation.objects.filter(
        client=client
    ).order_by('-date', '-time').first()

    # ── Average sentiment score for this client ────
    avg_client_sentiment = convs.aggregate(avg=Avg('sentiment_score'))['avg'] or 0

    context: dict[str, Any] = {
        'client_user': client,
        'diagnoses': diagnoses,
        'specifiers': specifiers,
        'documents': documents,
        'sentiment': sentiment_totals,
        'sentiment_pct': sentiment_pct,
        'sentiment_doughnut': sentiment_doughnut,
        'total_messages': total_messages,
        'topic_scores': topic_scores,
        'topic_radar': topic_radar,
        'chart_data': chart_data,
        'latest_conversation': latest_conversation,
        'avg_client_sentiment': round(avg_client_sentiment, 2),
    }
    return render(request, 'chat_analyzer/client/client_dashboard.html', context)

@client_required
def client_documents(request: HttpRequest) -> HttpResponse:
    """
    custom client document setup
    """
    from .models import DiagnosisDocument
    
    documents: QuerySet[DiagnosisDocument] = DiagnosisDocument.objects.filter(client=request.user).order_by('-upload_date')

    context: dict[str, Any] = {
        'documents': documents,
    }
    return render(request, 'chat_analyzer/client/client_documents.html', context)

@client_required
def client_therapist(request: HttpRequest) -> HttpResponse:
    """
    custom client therapist
    """
    # request.user already has the assigned_therapist foreign key
    return render(request, 'chat_analyzer/client/client_therapist.html', {'client_user': request.user})

@client_required
def client_settings(request: HttpRequest) -> HttpResponse:
    """
    custom client settings
    """
    client_user: User = request.user

    return render(request, 'chat_analyzer/client/client_settings.html', {'client_user': client_user})


# ╔════════════════════════════════════════════╗
# ║          RAG CHATBOT VIEWS 🤖              ║
# ╚════════════════════════════════════════════╝

@login_required
def chatbot_view(request):
    """Chatbot page — any authenticated user can ask treatment questions."""
    from .models import ChatQuery
    from .services.rag_service import get_collection_stats

    recent_queries = ChatQuery.objects.filter(user=request.user)[:10]
    stats = get_collection_stats()

    context = {
        'recent_queries': recent_queries,
        'vector_store_stats': stats,
    }
    # Different base templates per role
    if request.user.role == 'client':
        return render(request, 'chat_analyzer/client/chatbot.html', context)
    return render(request, 'chat_analyzer/chatbot.html', context)


@login_required
def chatbot_ask(request):
    """Handle chatbot question — POST only, returns JSON."""
    import time
    from .models import ChatQuery
    from .services.rag_service import query as rag_query

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)

    # FormData sends multipart — read question from POST, not body
    question = request.POST.get('question', '').strip()

    if not question:
        return JsonResponse({'error': 'Question cannot be empty'}, status=400)

    start_time = time.time()
    response = rag_query(question)
    elapsed_ms = int((time.time() - start_time) * 1000)

    # Log the query
    ChatQuery.objects.create(
        user=request.user,
        question=question,
        answer=response.answer,
        sources=response.sources,
        confidence=response.confidence,
        response_time_ms=elapsed_ms,
    )

    return JsonResponse({
        'answer': response.answer,
        'sources': response.sources,
        'confidence': round(response.confidence, 3),
        'response_time_ms': elapsed_ms,
    })


# ╔════════════════════════════════════════════╗
# ║    TREATMENT DOCUMENT UPLOAD (Doctor) 📄  ║
# ╚════════════════════════════════════════════╝

@login_required
def doctor_upload_document(request):
    """Doctor uploads a treatment PDF for the RAG knowledge base."""
    from .models import TreatmentDocument
    from .tasks import ingest_treatment_document
    from django.core.files.storage import default_storage

    if request.user.role not in ['doctor', 'admin']:
        return HttpResponseForbidden("Only doctors and admins can upload treatment documents.")

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        uploaded_file = request.FILES.get('file')

        if not title or not uploaded_file:
            messages.error(request, "Title and file are required.")
            return redirect('chat_analyzer:doctor_upload_document')

        if not uploaded_file.name.lower().endswith(('.pdf', '.txt', '.md')):
            messages.error(request, "Only PDF, TXT, and MD files are supported.")
            return redirect('chat_analyzer:doctor_upload_document')

        doc = TreatmentDocument.objects.create(
            uploaded_by=request.user,
            title=title,
            description=description,
            file=uploaded_file,
            status='pending',
        )

        # Fire the Celery task for async ingestion
        ingest_treatment_document.delay(doc.id)

        messages.success(request, f"📄 '{title}' uploaded — processing in background. It will be ready shortly.")
        return redirect('chat_analyzer:chatbot')

    # GET — show upload form + list existing documents
    documents = TreatmentDocument.objects.all().order_by('-created_at')
    context = {
        'documents': documents,
    }
    return render(request, 'chat_analyzer/doctor/upload_document.html', context)


@login_required
def doctor_start_chat(request, client_id):
    """Doctor starts a chat thread with a client (for emergency contact)."""
    from .models import User, ChatThread

    client = get_object_or_404(User, id=client_id, role='client')

    # Doctor can only message clients they diagnosed
    from .models import AutismDiagnosis
    if not AutismDiagnosis.objects.filter(client=client, diagnosed_by=request.user, is_active=True).exists():
        return HttpResponseForbidden("You can only message clients you have diagnosed.")

    thread, _ = ChatThread.objects.get_or_create(
        client=client,
        doctor=request.user,
        defaults={'therapist': None},
    )
    return redirect('chat_analyzer:chat_thread_detail', thread_id=thread.id)




