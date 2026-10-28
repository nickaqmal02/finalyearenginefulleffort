from django.urls import path
from . import views
from . import api_views
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
    path("dashboard/therapist/notifications/", views.therapist_notifications, name='therapist_notifications'),
    path("dashboard/notifications/<int:notification_id>/read/", views.mark_notification_read, name='mark_notification_read'),
    path("dashboard/notifications/read-all/", views.mark_all_notifications_read, name='mark_all_notifications_read'),
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
    path("dashboard/client/treatment-docs/", views.client_treatment_docs, name='client_treatment_docs'),
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
    path("reservation/", views.reservation_view, name="reservation"),
    path("reservation/ask/", views.reservation_ask, name="reservation_ask"),

# ╔════════════════════════════════════════════╗
# ║     TREATMENT DOCUMENT UPLOAD (Doctor) 📄  ║
# ╚════════════════════════════════════════════╝
    path("dashboard/doctor/upload-document/", views.doctor_upload_document, name="doctor_upload_document"),
    path("dashboard/doctor/chat/<int:client_id>/", views.doctor_start_chat, name="doctor_start_chat"),

# ╔════════════════════════════════════════════╗ 
# ║   API ENDPOINTS (for n8n chatbot) 🔌        ║ 
# ╚════════════════════════════════════════════╝ 
    path("api/check-availability/", api_views.check_availability, name="api_check_availability"),
    path("api/book-session/", api_views.book_session, name="api_book_session"),
    path("api/list-sessions/", api_views.list_sessions, name="api_list_sessions"),
    path("api/staff-schedule/", api_views.staff_schedule, name="api_staff_schedule"),
    path("api/cancel-booking/", api_views.cancel_booking, name="api_cancel_booking"),
    path("api/n8n-callback/", api_views.n8n_callback, name="api_n8n_callback"),
    path("api/poll-reply/", api_views.poll_reply, name="api_poll_reply"),
    path("reservation/bookings/refresh/", views.reservation_bookings_partial, name="reservation_bookings_refresh"),

]
