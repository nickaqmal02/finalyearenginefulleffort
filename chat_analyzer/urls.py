from django.urls import path
from . import views
from django.views.generic import RedirectView

app_name = 'chat_analyzer'

urlpatterns = [

    # public pages
    
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/admin/', views.admin_register, name='admin_register'),
    path('dashboard/admin', views.admin_dashboard, name='admin_dashboard'),


    # dashboard redirects 
    path('', views.login_view, name='home'),
    
    path('favicon.ico', RedirectView.as_view(url='https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/icons/file-earmark-bar-graph.svg')),



    # :::::::: ADMIN CLIENT MANAGEMENT :::::::::: #
    path('client/create/',views.admin_client_create, name='admin_client_create'),
    path('client/list/',views.admin_client_list, name='admin_client_list'),

    # admin-client delete
    path('clients/delete/<int:client_id>/delete/', views.admin_client_delete, name='admin_client_delete'),

    # admin-client edit
    path('clients/admin/<int:client_id>/edit/', views.admin_client_edit, name='admin_client_edit'),

    # Admin - Client Detail
    path('clients/admin/<int:client_id>/', views.admin_client_detail, name='admin_client_detail'),








    # ::::::::: ADMIN THERAPIST MANAGEMENT ::::::: 
    path('therapists/list/', views.admin_therapist_list, name='admin_therapist_list'),
    path('therapists/create/', views.admin_therapist_create, name='admin_therapist_create'),

    # simple function for toggle activate and deactivate for therapist
    path ('therapists/<int:therapist_id>/toggle/', views.admin_therapist_toggle, name='admin_therapist_toggle'),

    # admin-therapist edit
    path('therapists/admin/<int:therapist_id>/edit/', views.admin_therapist_edit, name='admin_therapist_edit'),

    # ADMIN-THERAPIST-DETAIL
    path('therapist/admin/<int:therapist_id>/detail/', views.admin_therapist_detail, name='admin_therapist_detail'),
]