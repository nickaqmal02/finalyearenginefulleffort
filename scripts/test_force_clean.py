import sys, os, django
sys.path.insert(0, "/Users/apple/degree/finalyearengineredo")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finalyearengineredo.settings")
django.setup()
from chat_analyzer.models import Conversation
from chat_analyzer.services.text_cleaner import batch_clean_conversations

s, t = batch_clean_conversations(force=True)
print(f"force batch_clean: sentiment={s} topic={t}")

c = Conversation.objects.get(id=3686)
print("[3686] after:", repr(c.cleaned_text_topic))
