import sys, os, django
sys.path.insert(0, "/Users/apple/degree/finalyearengineredo")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finalyearengineredo.settings")
django.setup()
from chat_analyzer.models import Conversation, MessageTopic, Topic
import pathlib

# coverage
client_convs = Conversation.objects.filter(client__isnull=False)
with_topic = MessageTopic.objects.filter(conversation__client__isnull=False).values_list("conversation_id", flat=True).distinct()
print(f"client conversations: {client_convs.count()}, with topics: {len(set(with_topic))}")

# topic names + name-leak check in cleaned_text_topic
names = set()
p = pathlib.Path("/Users/apple/degree/finalyearengineredo/chat_analyzer/data/person_names.txt")
for line in p.read_text().splitlines():
    line = line.split("#")[0].strip()
    if line:
        names.add(line)

print("\nTopics:")
for t in Topic.objects.all():
    n = MessageTopic.objects.filter(topic=t).count()
    print(f"  [{t.status}] {t.name} -> {n} rows")

leaks = [(c.id, w) for c in Conversation.objects.exclude(cleaned_text_topic__isnull=True).exclude(cleaned_text_topic="")
         for w in c.cleaned_text_topic.split()
         if "".join(ch for ch in w if ch.isalnum()).lower() in names]
print(f"\nName leaks in cleaned_text_topic: {len(leaks)}")
print("sample leaks:", leaks[:8])
