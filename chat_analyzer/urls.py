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
    path("chat/threads/", views.therapist_chat_threads, name="therapist_chat_threads"),
    path("chat/threads/<int:thread_id>/", views.chat_thread_detail, name="chat_thread_detail"),
    path("doctor/chat/threads/", views.doctor_chat_threads, name="doctor_chat_threads"),

# ╔════════════════════════════════════════════╗ 
# ║          DOCTOR SECTION PATH 😇            ║ 
# ╚════════════════════════════════════════════╝ 

# ╔════════════════════════════════════════════╗ 
# ║          CLIENT SECTION PATH 😃          ║ 
# ╚════════════════════════════════════════════╝ 
#   
    path("dashboard/client/documents/", views.client_documents, name='client_documents'),
    path("dashboard/client/therapist/", views.client_therapist, name='client_therapist'),
    path("dashboard/client/settings/", views.client_settings, name='client_settings'),
    path("client/chat/<int:thread_id>/", views.chat_thread_detail, name='client_chat_thread'),
    path("chat/start/<int:client_id>/", views.start_chat_with_client, name="start_chat_with_client"),
    path("client/chat/start/", views.start_chat_with_therapist, name="client_start_chat"),
    path("client/messages/", views.client_messages, name="client_messages"),

# ╔════════════════════════════════════════════╗
# ║          RAG CHATBOT 🤖                    ║
# ╚════════════════════════════════════════════╝
    path("chatbot/", views.chatbot_view, name="chatbot"),
    path("chatbot/ask/", views.chatbot_ask, name="chatbot_ask"),

# ╔════════════════════════════════════════════╗
# ║     TREATMENT DOCUMENT UPLOAD (Doctor) 📄  ║
# ╚════════════════════════════════════════════╝
    path("dashboard/doctor/upload-document/", views.doctor_upload_document, name="doctor_upload_document"),
    path("dashboard/doctor/chat/<int:client_id>/", views.doctor_start_chat, name="doctor_start_chat"),

]
