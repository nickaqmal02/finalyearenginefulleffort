from django.apps import AppConfig


class ChatAnalyzerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chat_analyzer'
    verbose_name = "🏥 Autism Center Management"

    def ready(self):
        # register the signals handlers on app startup
        import chat_analyzer.signals
