from django.shortcuts import render, redirect, get_object_or_404
from typing import Any
from django.db.models import QuerySet
from django.contrib import messages
from datetime import datetime
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie, csrf_exempt
from django.contrib.auth.forms import AuthenticationForm
from .forms import CustomLoginForm, CustomSignUpForm, UploadChatForm, UploadDocumentForm
from .models import User
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
    """Admin dasboard : only accessible to admin """
    context = {
        'total_users': User.objects.count(),
        'total_therapists': User.objects.filter(role='therapist').count(),
    }
    return render(request, 'chat_analyzer/admin/admin_dashboard.html', context)

@therapist_required
def therapist_dashboard(request):
    """Only Therapist can access this section"""
    context = {
        'assigned_clients': request.user.assigned_clients.all(),
    }
    return render(request, 'chat_analyzer/therapist/therapist_dashboard.html', context)

@doctor_required
def doctor_dashboard(request):
    """Doctor dashboard"""
    return render(request, 'chat_analyzer/doctor/doctor_dashboard.html', context)

@client_required
def client_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Displays the dashboard for a specific client.
    Shows their info and recent conversation topics.
    """
    from .models import AutismDiagnosis, ClientSpecifier, DiagnosisDocument, Conversation, ClientTopicScore, User
    from django.db.models import Count, Sum, Q
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
        .annotate(score=Sum('sentiment_score'))
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

    chart_data: str = json.dumps({
        "labels": date_strings,
        "datasets": [{
            "label": "Sentiment Progress",
            "data": scores,
            "borderColor": "#10b981",
            "backgroundColor": "rgba(16, 185, 129, 0.1)",
            "fill": True,
            "tension": 0.3,
        }],
    })

    context: dict[str, Any] = {
        'client_user': client,
        'diagnoses': diagnoses,
        'specifiers': specifiers,
        'documents': documents,
        'sentiment': sentiment_totals,
        'total_messages': total_messages,
        'topic_scores': topic_scores,
        'chart_data': chart_data,
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




