"""Quick probe: do real names survive the cleaner at train time?"""
import os, sys, django

sys.path.insert(0, "/Users/apple/degree/finalyearengineredo")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finalyearengineredo.settings")
django.setup()

from chat_analyzer.services.text_cleaner import clean_for_topic_modeling, clean_for_sentiment

tests = [
    "Ustaz Adam kata affan dah boleh duduk tenang",
    "Puan Aina Razak, adik Adam pergi terapi pagi tadi",
    "Dr Kumar suruh buat latihan motor setiap hari",
    "anak saya tidur pukul 3 pagi semalam, risau betul",
]
for t in tests:
    print(repr(t))
    print("  topic:    ", repr(clean_for_topic_modeling(t)))
    print("  sentiment:", repr(clean_for_sentiment(t)))
    print()
