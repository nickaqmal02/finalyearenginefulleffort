import os, sys, django
sys.path.insert(0, "/Users/apple/degree/finalyearengineredo")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finalyearengineredo.settings")
django.setup()
from chat_analyzer.models import User
for u in User.objects.all().order_by("id"):
    print(u.id, "|", u.username, "|", u.first_name, u.last_name, "|", u.role if hasattr(u, "role") else "")
