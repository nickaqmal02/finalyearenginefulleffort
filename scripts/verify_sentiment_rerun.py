import sys, os, django
sys.path.insert(0, "/Users/apple/degree/finalyearengineredo")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finalyearengineredo.settings")
django.setup()
from chat_analyzer.models import Conversation
from collections import Counter
import pathlib

# load blocklist tokens
names = set()
p = pathlib.Path("/Users/apple/degree/finalyearengineredo/chat_analyzer/data/person_names.txt")
for line in p.read_text().splitlines():
    line = line.split("#")[0].strip()
    if line:
        names.add(line)

labels = Counter()
no_score = 0
leaks = []
for c in Conversation.objects.all():
    labels[c.sentiment] += 1
    if c.sentiment and c.sentiment_score is None:
        no_score += 1
    if c.cleaned_text:
        for w in c.cleaned_text.split():
            bare = "".join(ch for ch in w if ch.isalnum())
            if bare.lower() in names:
                leaks.append((c.id, w, c.cleaned_text[:60]))

print("Label distribution:", dict(labels))
print("Rows with label but no score:", no_score)
print("Name leaks in cleaned_text:", len(leaks))
for row in leaks[:10]:
    print("  ", row)

# sample row for eyeball proof
sample = Conversation.objects.filter(sentiment__isnull=False).first()
print("\nSample:", sample.sentiment, sample.sentiment_score, sample.sentiment_confidence)
print("  raw:", sample.message[:70])
print("  cleaned:", sample.cleaned_text[:70])
