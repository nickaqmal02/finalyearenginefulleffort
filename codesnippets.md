## using decorators approach for cleaner one

from django.urls import path
from . import views

app_name = 'chat_analyzer'

urlpatterns = [
    # ================================
    # 1. WELCOMING PAGE 😊
    # ================================
    path('', views.welcome_view, name='welcome_view'),
    
    # ================================
    # 2. AUTHENTICATION 🔑
    # ================================
    path('login/', views.login_view, name='login_view'),
    path('logout/', views.logout_view, name='logout_view'),
    path('signup/', views.signup_view, name='signup_view'),
    
    # ================================
    # 3. DASHBOARDS FOR EACH ROLE 🔒
    # ================================
    # Admin Dashboard
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Therapist Dashboard
    path('therapist-dashboard/', views.therapist_dashboard, name='therapist_dashboard'),
    
    # Doctor Dashboard
    path('doctor-dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    
    # Client Dashboard
    path('client-dashboard/', views.client_dashboard, name='client_dashboard'),
    
    # ================================
    # 4. USER MANAGEMENT (Admin Only) 👥
    # ================================
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_detail, name='user_detail'),
    path('users/<int:user_id>/edit/', views.user_edit, name='user_edit'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    
    # ================================
    # 5. THERAPIST MANAGEMENT (Admin & Therapist) 👨‍⚕️
    # ================================
    path('therapists/', views.therapist_list, name='therapist_list'),
    path('therapists/<int:therapist_id>/', views.therapist_detail, name='therapist_detail'),
    path('therapists/<int:therapist_id>/assign/', views.assign_client, name='assign_client'),
    
    # ================================
    # 6. CLIENT MANAGEMENT (Admin, Therapist, Doctor) 👤
    # ================================
    path('clients/', views.client_list, name='client_list'),
    path('clients/<int:client_id>/', views.client_detail, name='client_detail'),
    path('clients/<int:client_id>/edit/', views.client_edit, name='client_edit'),
    
    # ================================
    # 7. APPOINTMENT MANAGEMENT 📅
    # ================================
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/create/', views.appointment_create, name='appointment_create'),
    path('appointments/<int:appointment_id>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:appointment_id>/edit/', views.appointment_edit, name='appointment_edit'),
    path('appointments/<int:appointment_id>/delete/', views.appointment_delete, name='appointment_delete'),
    
    # ================================
    # 8. MESSAGING SYSTEM 💬
    # ================================
    path('messages/', views.message_list, name='message_list'),
    path('messages/create/', views.message_create, name='message_create'),
    path('messages/<int:message_id>/', views.message_detail, name='message_detail'),
    path('messages/<int:message_id>/reply/',iewsessage_reply, name='message_reply'),
    
    # ================================
    # 9. REPORTING & ANALYTICS 📊
    # ================================
    path('reports/', views.report_list, name='report_list'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),
    path('reports/<int:report_id>/download/', views.report_download, name='report_download'),
    
    # ================================
    # 10. API ENDPOINTS (Optional) 🔌
    # ================================
    # path('api/users/', views.api_user_list, name='api_user_list'),
    # path('api/appointments/', views.api_appointment_list, name='api_appointment_list'),
]




#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
##### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
##### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
##### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
##### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from .decorators import admin_required, therapist_required, doctor_required, client_required
from .models import User
from .forms import CustomLoginForm, CustomSignUpForm

#========================
# 1. WELCOMING PAGE VIEWS 😊
# =======================
def welcome_view(request):
    return render(request, 'chat_analyzer/welcome.html')

# ================================
# 2. AUTHENTICATION SECTION VIEWS 🔑
# ================================

def login_view(request):
    """Custom login view with role-based redirect"""
    
    # If user is already logged in, redirect to their dashboard
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
    
    if request.method == "POST":
        form = CustomLoginForm(request, data=request.POST)
        
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {username}!")
                
                # Check for 'next' parameter first
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                
                # Role-based redirect
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
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = CustomLoginForm()

    return render(request, 'chat_analyzer/login.html', {'form': form})


def logout_view(request):
    """Custom logout view"""
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('chat_analyzer:login_view')


def signup_view(request):
    """Custom signup view with role-based registration"""
    
    # If user is already logged in, redirect to dashboard
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
    
    if request.method == 'POST':
        form = CustomSignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Log the user in after registration
            login(request, user)
            messages.success(request, f"Account created successfully! Welcome, {user.username}!")
            
            # Redirect based on role
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
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomSignUpForm()
    
    return render(request, 'chat_analyzer/signup.html', {'form': form})

# ===========================
# 3. DASHBOARD FOR EACH ROLE 🔒 using decorators
# ===========================

@admin_required
def admin_dashboard(request):
    """Admin dashboard : only accessible to admin"""
    context = {
        'total_users': User.objects.count(),
        'total_therapists': User.objects.filter(role='therapist').count(),
        'total_doctors': User.objects.filter(role='doctor').count(),
        'total_clients': User.objects.filter(role='client').count(),
    }
    return render(request, 'chat_analyzer/admin_dashboard.html', context)

@therapist_required
def therapist_dashboard(request):
    """Only Therapist can access this section"""
    context = {
        'assigned_clients': request.user.assigned_clients.all(),
        'total_clients': request.user.assigned_clients.count(),
    }
    return render(request, 'chat_analyzer/therapist_dashboard.html', context)

@doctor_required
def doctor_dashboard(request):
    """Doctor dashboard - only accessible to doctors"""
    context = {
        'patients': [],  # Add your logic here
    }
    return render(request, 'chat_analyzer/doctor_dashboard.html', context)

@client_required
def client_dashboard(request):
    """Client dashboard"""
    context = {
        'assigned_therapist': request.user.assigned_therapist,
        'last_visit': request.user.last_visit,
    }
    return render(request, 'chat_analyzer/client_dashboard.html', context)



###### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
###### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
###### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
### ADMIN SECTION SNIPPETS AND STUCTURE :::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
#### ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

> started at: 06 AUG 2026 1907H 

## THE STUCTURE
templates/chat_analyzer/
├── base.html                    # Main base template
├── admin/
│   ├── base_admin.html         # Admin base with sidebar
│   ├── partials/
│   │   ├── admin_sidebar.html  # Sidebar component
│   │   └── admin_header.html   # Header component
│   └── pages/
│       ├── dashboard.html
│       ├── users.html
│       └── settings.html
└── auth/
    ├── login.html
    └── signup.html

### CODE SNIPPETS

> BASE.html
<!-- Admin Base Template with Sidebar -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Admin Dashboard{% endblock %} - Chat Analyzer</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- DaisyUI -->
    <link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />
    
    <!-- Tailwind Browser -->
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    
    {% load heroicons %}
    
    <!-- Custom CSS -->
    {% block extra_css %}{% endblock %}
    
    <style>
        .sidebar {
            transition: all 0.3s ease;
        }
        .sidebar.collapsed {
            width: 64px !important;
        }
        .sidebar.collapsed .sidebar-text {
            display: none;
        }
        .sidebar.collapsed .sidebar-icon {
            margin-right: 0;
        }
        .main-content {
            transition: all 0.3s ease;
        }
        .main-content.expanded {
            margin-left: 64px;
        }
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                position: fixed;
                z-index: 50;
                height: 100vh;
            }
            .sidebar.open {
                transform: translateX(0);
            }
        }
    </style>
</head>

<body class="bg-gray-100 dark:bg-gray-900">
    <div class="flex h-screen overflow-hidden">
        <!-- Sidebar -->
        {% include "chat_analyzer/admin/partials/admin_sidebar.html" %}
        
        <!-- Main Content -->
        <div class="flex-1 flex flex-col overflow-hidden">
            <!-- Header -->
            {% include "chat_analyzer/admin/partials/admin_header.html" %}
            
            <!-- Page Content -->
            <main class="flex-1 overflow-y-auto p-4 md:p-6">
                {% block content %}
                {% endblock %}
            </main>
        </div>
    </div>
    
    <!-- Mobile Menu Overlay -->
    <div id="sidebar-overlay" class="fixed inset-0 bg-black bg-opacity-50 z-40 hidden lg:hidden" onclick="toggleSidebar()"></div>
    
    <script>
        // Toggle sidebar on mobile
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebar-overlay');
            sidebar.classList.toggle('open');
            overlay.classList.toggle('hidden');
        }
        
        // Toggle sidebar collapse
        function toggleCollapse() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('collapsed');
        }
        
        // Close sidebar on resize
        window.addEventListener('resize', function() {
            if (window.innerWidth > 1024) {
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementById('sidebar-overlay');
                sidebar.classList.remove('open');
                overlay.classList.add('hidden');
            }
        });
    </script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>

> SIDEBAR.html

<!-- Admin Base Template with Sidebar -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Admin Dashboard{% endblock %} - Chat Analyzer</title>
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- DaisyUI -->
    <link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />
    
    <!-- Tailwind Browser -->
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    
    {% load heroicons %}
    
    <!-- Custom CSS -->
    {% block extra_css %}{% endblock %}
    
    <style>
        .sidebar {
            transition: all 0.3s ease;
        }
        .sidebar.collapsed {
            width: 64px !important;
        }
        .sidebar.collapsed .sidebar-text {
            display: none;
        }
        .sidebar.collapsed .sidebar-icon {
            margin-right: 0;
        }
        .main-content {
            transition: all 0.3s ease;
        }
        .main-content.expanded {
            margin-left: 64px;
        }
        @media (max-width: 768px) {
            .sidebar {
                transform: translateX(-100%);
                position: fixed;
                z-index: 50;
                height: 100vh;
            }
            .sidebar.open {
                transform: translateX(0);
            }
        }
    </style>
</head>

<body class="bg-gray-100 dark:bg-gray-900">
    <div class="flex h-screen overflow-hidden">
        <!-- Sidebar -->
        {% include "chat_analyzer/admin/partials/admin_sidebar.html" %}
        
        <!-- Main Content -->
        <div class="flex-1 flex flex-col overflow-hidden">
            <!-- Header -->
            {% include "chat_analyzer/admin/partials/admin_header.html" %}
            
            <!-- Page Content -->
            <main class="flex-1 overflow-y-auto p-4 md:p-6">
                {% block content %}
                {% endblock %}
            </main>
        </div>
    </div>
    
    <!-- Mobile Menu Overlay -->
    <div id="sidebar-overlay" class="fixed inset-0 bg-black bg-opacity-50 z-40 hidden lg:hidden" onclick="toggleSidebar()"></div>
    
    <script>
        // Toggle sidebar on mobile
        function toggleSidebar() {
            const sidebar = document.getElementById('sidebar');
            const overlay = document.getElementById('sidebar-overlay');
            sidebar.classList.toggle('open');
            overlay.classList.toggle('hidden');
        }
        
        // Toggle sidebar collapse
        function toggleCollapse() {
            const sidebar = document.getElementById('sidebar');
            sidebar.classList.toggle('collapsed');
        }
        
        // Close sidebar on resize
        window.addEventListener('resize', function() {
            if (window.innerWidth > 1024) {
                const sidebar = document.getElementById('sidebar');
                const overlay = document.getElementByI
                sidebar.classList.remove('open');
                overlay.classList.add('hidden');
            }
        });
    </script>
    
    {% block extra_js %}{% endblock %}
</body>
</html>


> ADMIN_SIDEBAR.html
{% load heroicons %}

<!-- Sidebar -->
<aside id="sidebar" class="sidebar bg-gray-900 dark:bg-gray-800 text-white w-64 flex-shrink-0">
    <div class="flex flex-col h-full">
        <!-- Logo -->
        <div class="flex items-center justify-between p-4 border-b border-gray-700">
            <a href="{% url 'chat_analyzer:admin_dashboard' %}" class="flex items-center space-x-2">
                {% heroicon_outline "chat-bubble-left-right" class="w-8 h-8 text-blue-400" %}
                <span class="sidebar-text text-xl font-bold">ChatAnalyzer</span>
            </a>
            <!-- Collapse Button -->
            <button onclick="toggleCollapse()" class="hidden lg:block hover:bg-gray-700 p-1 rounded">
                {% heroicon_outline "chevron-left" class="w-5 h-5" %}
            </button>
        </div>
        
        <!-- Navigation -->
        <nav class="flex-1 overflow-y-auto p-4 space-y-1">
            <!-- Dashboard -->
            <a href="{% url 'chat_analyzer:admin_dashboard' %}" 
               class="flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700 {% if request.resolver_match.url_name == 'admin_dashboard' %}bg-gray-700{% endif %}">
                {% heroicon_outline "home" class="sidebar-icon w-5 h-5 flex-shrink-0" %}
                <span class="sidebar-text">Dashboard</span>
            </a>
            
            <!-- Users -->
            <a href="{% url 'chat_analyzer:user_list' %}" 
               class="flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700 {% if 'user' in request.resolver_match.url_name %}bg-gray-700{% endif %}">
                {% heroicon_outline "users" class="sidebar-icon w-5 h-5 flex-shrink-0" %}
                <span class="sidebar-text">Users</span>
            </a>
            
            <!-- Therapists -->
            <a href="{% url 'chat_analyzer:therapist_list' %}" 
               class="flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700 {% if 'therapist' in request.resolver_match.url_name %}bg-gray-700{% endif %}">
                {% heroicon_outline "user-circle" class="sidebar-icon w-5 h-5 flex-shrink-0" %}
                <span class="sidebar-text">Therapists</span>
            </a>
            
            <!-- Doctors -->
            <a href="{% url 'chat_analyzer:doctor_list' %}" 
               class="flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700 {% if 'doctor' in request.resolver_match.url_name %}bg-gray-700{% endif %}">
                {% heroicon_outline "briefcase" class="sidebar-icon w-5 h-5 flex-shrink-0" %}
                <span class="sidebar-text">Doctors</span>
            </a>
            
            <!-- Clients -->
            <a href="{% url 'chat_analyzer:client_list' %}" 
               class="flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700 {% if 'client' in request.resolver_match.url_name %}bg-gray-700{% endif %}">
                {% heroicon_outline "user" class="sidebar-icon w-5 h-5 flex-shrink-0" %}
                <span class="sidebar-text">Clients</span>
            </a>
            
            <!-- Divider -->
            <hr class="my-4 border-gray-700">
            
            <!-- Appointments -->
            <a href="{% url 'chat_analyzer:appointment_list' %}" 
               class="flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700 {% if 'appointment' in request.resolver_match.url_name %}bg-gray-700{% endif %}">
                {% heroicon_outline "calendar" class="sidebar-icon w-5 h-5 flex-shrink-0" %}
                <span class="sidebar-text">Appointments</span>
            </a>
            
            <!-- Messages -->
            <a href="{% url 'chat_analyzer:message_list' %}" 
               class="flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700 {% if 'message' in request.resolver_match.url_name %}bg-gray-700{% endif %}">
                {% heroicon_outline "chat-bubble-left-right" class="sidebar-icon w-5 h-5 flex-shrink-0" %}
                <span class="sidebar-text">Messages</span>
                <span class="sidebar-text ml-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">3</span>
            </a>
            
            <!-- Reports -->
            <a href="{% url 'chat_analyzer:report_list' %}" 
               class="flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700 {% if 'report' in request.resolver_match.url_name %}bg-gray-700{% endif %}">
                {% heroicon_outline "chart-bar" class="sidebar-icon w-5 h-5 flex-shrink-0" %}
                <span class="sidebar-text">Reports</span>
            </a>
            
            <!-- Settings -->
            <hr class="my-4 border-gray-700">
            <a href="{% url 'chat_analyzer:settings' %}" 
               class="flex items-center space-x-3 px-3 py-2.5 rounded-lg transition-colors duration-200 hover:bg-gray-700 {% if 'settings' in request.resolver_match.url_name %}bg-gray-700{% endif %}">
                {% heroicon_outline "cog-6-tooth" class="sidebar-icon w-5 h-5 flex-shrink-0" %}
                <span class="sidebar-text">Settings</span>
            </a>
        </nav>
        
        <!-- User Footer -->
        <div class="p-4 border-t border-gray-700">
            <div class="flex items-center space-x-3 px-2 py-2 rounded-lg hover:bg-gray-700 cursor-pointer">
                <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white font-semibold">
                    {{ user.username|first|upper }}
                </div>
                <div class="sidebar-text flex-1">
                    <p class="text-sm font-medium">{{ user.get_full_name|default:user.username }}</p>
                    <p class="text-xs text-gray-400">{{ user.role|title }}</p>
                </div>
                <a href="{% url 'chat_analyzer:logout_view' %}" class="sidebar-text hover:text-red-400">
                    {% heroicon_outline "arrow-right-on-rectangle" class="w-5 h-5" %}
                </a>
            </div>
        </div>
    </div>
</aside>



# ::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

{% load heroicons %}

{% block content %}
<div class="flex h-screen bg-gray-900 text-white">

  <!-- Sidebar with daisyUI glass -->
  <div class="w-72 glass p-4 flex flex-col border-r border-white/10">

    <!-- Logo / Brand -->
    <div class="flex items-center gap-3 mb-6 px-2">
      <div class="w-8 h-8 bg-gradient-to-br from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
        {% heroicon_solid "musical-note" class="w-5 h-5 text-white" %}
      </div>
      <span class="text-xl font-bold">MusicApp</span>
    </div>

    <!-- Search Bar -->
    <div class="relative mb-6">
      <div class="absolute inset-y-0 left-3 flex items-center pointer-events-none">
        {% heroicon_outline "magnifying-glass" class="w-5 h-5 text-gray-400" %}
      </div>
      <input 
        type="text" 
        placeholder="Search" 
        class="w-full bg-white/5 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-400 border border-white/10 focus:outline-none focus:border-purple-500 focus:ring-1 focus:ring-purple-500"
      >
    </div>

    <!-- Navigation -->
    <nav class="space-y-1 mb-6">
      <a href="#" class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/10 transition group">
        <span class="text-gray-400 group-hover:text-white">{% heroicon_outline "home" class="w-5 h-5" %}</span>
        <span class="text-sm font-medium">Home</span>
      </a>
      
      <a href="#" class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-white/10 transition group">
        <span class="text-gray-400 group-hover:text-white">{% heroicon_outline "plus-circle" class="w-5 h-5" %}</span>
        <span class="text-sm font-medium">New</span>
      </a>
      
      <a href="#" class="flex items-center gap-3 px-3 py-2.5 rounded-lg bg-white/10 transition group">
        <span class="text-white">{% heroicon_outline "radio" class="w-5 h-5" %}</span>
        <span class="text-sm font-medium text-white">Radio</span>
      </a>
    </nav>

    <!-- Divider -->
    <div class="h-px bg-white/10 mb-4"></div>

    <!-- Library Section -->
    <div class="flex-1 overflow-y-auto">
      <div class="flex items-center justify-between px-2 mb-3">
        <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Library</span>
        <button class="text-gray-400 hover:text-white">
          {% heroicon_outline "plus" class="w-4 h-4" %}
        </button>
      </div>

      <div class="space-y-0.5">
        <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 transition group">
          <span class="text-gray-400 group-hover:text-white">{% heroicon_outline "clock" class="w-5 h-5" %}</span>
          <span class="text-sm">Recently Added</span>
        </a>
        
        <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 transition group">
          <span class="text-gray-400 group-hover:text-white">{% heroicon_outline "user" class="w-5 h-5" %}</span>
          <span class="text-sm">Artists</span>
        </a>
        
        <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 transition group">
          <span class="text-gray-400 group-hover:text-white">{% heroicon_outline "folder" class="w-5 h-5" %}</span>
          <span class="text-sm">Albums</span>
        </a>
        
        <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 transition group">
          <span class="text-gray-400 group-hover:text-white">{% heroicon_outline "musical-note" class="w-5 h-5" %}</span>
          <span class="text-sm">Songs</span>
        </a>
      </div>

      <!-- Divider -->
      <div class="h-px bg-white/10 my-4"></div>

      <!-- Playlists Section -->
      <div class="flex items-center justify-between px-2 mb-3">
        <span class="text-xs font-semibold text-gray-400 uppercase tracking-wider">Playlists</span>
        <button class="text-gray-400 hover:text-white">
          {% heroicon_outline "plus" class="w-4 h-4" %}
        </button>
      </div>

      <div class="space-y-0.5">
        <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 transition group">
          <span class="text-gray-400 group-hover:text-white">{% heroicon_outline "play-circle" class="w-5 h-5" %}</span>
          <span class="text-sm">All Playlists</span>
        </a>
      </div>
    </div>

    <!-- User Profile at Bottom -->
    <div class="border-t border-white/10 pt-3 mt-3">
      <a href="#" class="flex items-center gap-3 px-3 py-2 rounded-lg hover:bg-white/10 transition group">
        <div class="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-xs font-bold">
          NA
        </div>
        <div class="flex-1">
          <p class="text-sm font-medium">nicki aqmal</p>
          <p class="text-xs text-gray-400">View Profile</p>
        </div>
        <span class="text-gray-400">{% heroicon_outline "chevron-down" class="w-4 h-4" %}</span>
      </a>
    </div>

  </div>

  <!-- Main Content Area -->
  <div class="flex-1 p-6 overflow-y-auto">
    <h1 class="text-2xl font-bold">Welcome back!</h1>
    <p class="text-gray-400 mt-2">Select a playlist or start exploring</p>
  </div>

</div>
{% endblock %}
