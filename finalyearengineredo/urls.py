# HERE IS MAIN URL OF THIS
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from debug_toolbar.toolbar import debug_toolbar_urls

urlpatterns = [
    path('admin/', admin.site.urls), # django built in admin
    path('',include('chat_analyzer.urls')), # our apps url
] + debug_toolbar_urls()

# serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
