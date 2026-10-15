from django.urls import path
from . import views
from django.views.generic import RedirectView

app_name = 'chat_analyzer'

urlpatterns = [

# ╔════════════════════════════════════════════╗ 
# ║            WELCOMING VIEW 🙃               ║ 
# ╚════════════════════════════════════════════╝ 
    path("", views.welcome_view, name="welcome_view"),

# ╔════════════════════════════════════════════╗ 
# ║        AUTHENTICATION SECTION 🥸           ║ 
# ╚════════════════════════════════════════════╝ 
    path("login/", views.login_view, name='login_view'),
    path("logout/", views.logout_view, name='logout_view'),
    path("signup/", views.signup_view, name='signup_view'),
    
# ╔════════════════════════════════════════════╗ 
# ║        DASHBOARD FOR EACH ROLE 🔒          ║ 
# ╚════════════════════════════════════════════╝ 
    path("dashboard/admin/", views.admin_dashboard, name='admin_dashboard'),
    path("dashboard/therapist/", views.therapist_dashboard, name='therapist_dashboard'),
    path("dashboard/therapist/client/<int:client_id>/", views.therapist_client_detail, name='therapist_client_detail'),
    path("dashboard/therapist/upload/", views.therapist_upload_chat, name='therapist_upload_chat'),
    path("dashboard/doctor/", views.doctor_dashboard, name='doctor_dashboard'),
    path("dashboard/doctor/approve/<int:doc_id>/", views.doctor_approve_document, name='doctor_approve_document'),
    path("dashboard/client/", views.client_dashboard, name='client_dashboard'),

# ╔════════════════════════════════════════════╗ 
# ║         ADMIN SECTION PATH ⚔️              ║ 
# ╚════════════════════════════════════════════╝ 

#********************************************
# ADMIN CREATING USER 🤝
#********************************************



# ╔════════════════════════════════════════════╗ 
# ║     THERAPIST SECTION PATH 😮‍💨              ║ 
# ╚════════════════════════════════════════════╝ 

# ╔════════════════════════════════════════════╗ 
# ║          DOCTOR SECTION PATH 😇            ║ 
# ╚════════════════════════════════════════════╝ 

# ╔════════════════════════════════════════════╗ 
# ║          CLIENT SECTION PATH 😃          ║ 
# ╚════════════════════════════════════════════╝ 
    path("dashboard/client/documents/", views.client_documents, name='client_documents'),
    path("dashboard/client/therapist/", views.client_therapist, name='client_therapist'),
    path("dashboard/client/settings/", views.client_settings, name='client_settings'),
]
