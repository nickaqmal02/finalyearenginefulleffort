import sys, os, django
sys.path.insert(0, "/Users/apple/degree/finalyearengineredo")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finalyearengineredo.settings")
django.setup()
from chat_analyzer.models import Conversation
from chat_analyzer.services.text_cleaner import clean_for_topic_modeling

for cid in [3695, 3686, 3643, 3584, 3462]:
    c = Conversation.objects.get(id=cid)
    print(f"[{cid}]")
    print("  raw:     ", repr(c.message))
    print("  in DB:   ", repr(c.cleaned_text_topic))
    print("  fresh:   ", repr(clean_for_topic_modeling(c.message)))
    print()
