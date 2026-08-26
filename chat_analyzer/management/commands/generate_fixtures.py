"""
Generate WhatsApp-format chat fixtures from labeled sentiment data.

Reads:  chat_analyzer/data/labeled_data/labeledsentimentdatatwo_balanced.csv
Writes: fixtures/*.txt  (WhatsApp bracket format: [DD/MM/YYYY, HH:MM:SS] sender: message)

Produces:
  - 5 individual client-therapist chat files (1:1 sessions)
  - 1 admin group-chat file (multiple parents messaging admin)
  - 1 manifest.json mapping file -> client_id -> assigned topics

The generator REUSES the Sastrawi stemming + keyword overlap logic
from TopicMapper to assign each labeled message to one of the 12
therapy topics. Messages with no topic match are skipped.

Usage:
  python manage.py generate_fixtures
  python manage.py generate_fixtures --messages-per-client 30
"""
import csv
import json
import os
import random
from datetime import datetime, timedelta

from django.core.management.base import BaseCommand
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

from chat_analyzer.models import Topic

# Topic -> (parent name, child name) for the 5 fixture clients
# Keyed by client_id from the DB
CLIENT_ASSIGNMENTS = {
    10: {
        "parent": "Ahmad Fauzi",
        "child": "Arif",
        "topics": ["Eating Habits & Food Acceptance", "Sleep Patterns", "Tantrum & Behavior Management"],
        "therapist": "Aina Razak",
    },
    11: {
        "parent": "Siti Aishah",
        "child": "Maya",
        "topics": ["Speech & Communication Development", "Social Interaction", "Parental Emotions"],
        "therapist": "Daniel Tan",
    },
    12: {
        "parent": "Ravi Kumar",
        "child": "Anita",
        "topics": ["School & Academic Progress", "Therapy Progress", "Sensory Integration"],
        "therapist": "Farah Ismail",
    },
    13: {
        "parent": "Lim Mei Ling",
        "child": "Jun",
        "topics": ["Physical Development", "Family Environment", "Treatment Methods"],
        "therapist": "Kumar Raj",
    },
    14: {
        "parent": "Sarah Tan",
        "child": "child",  # placeholder, will be set
        "topics": ["Parental Emotions", "Tantrum & Behavior Management", "Sleep Patterns"],
        "therapist": "Aina Razak",
    },
}


class Command(BaseCommand):
    help = "Generate WhatsApp-format chat fixtures from labeled sentiment data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--messages-per-client",
            type=int,
            default=25,
            help="Number of messages per client-therapist chat (default: 25)",
        )
        parser.add_argument(
            "--group-size",
            type=int,
            default=40,
            help="Number of messages for admin group chat (default: 40)",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="fixtures",
            help="Output directory for .txt files (default: fixtures)",
        )

    def handle(self, *args, **options):
        messages_per_client = options["messages_per_client"]
        group_size = options["group_size"]
        output_dir = options["output_dir"]

        self.stdout.write(self.style.MIGRATE_HEADING("🏗️  Chat Fixture Generator"))
        self.stdout.write("=" * 60)

        # --- 1. Load labeled data ---
        csv_path = os.path.join(
            "chat_analyzer", "data", "labeled_data",
            "labeledsentimentdatatwo_balanced.csv"
        )
        if not os.path.exists(csv_path):
            self.stdout.write(self.style.ERROR(f"❌ Labeled data not found: {csv_path}"))
            return

        labeled_rows = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                labeled_rows.append({
                    "text": row["text"].strip(),
                    "label": int(row["label"]),
                })

        self.stdout.write(f"📖 Loaded {len(labeled_rows)} labeled messages")
        self.stdout.write("   Labels: 0=negative, 1=neutral, 2=positive")

        # --- 2. Build stemmer + topic keyword map ---
        stemmer = StemmerFactory().create_stemmer()

        topics = list(Topic.objects.filter(is_active=True))
        self.stdout.write(f"🏷️  Loaded {len(topics)} therapy topics")

        # Pre-stem topic keywords into sets
        topic_stemmed = {}
        for topic in topics:
            stemmed = set()
            for kw in topic.keywords:
                stemmed.add(stemmer.stem(kw.lower()))
            topic_stemmed[topic.name] = stemmed

        # --- 3. Match each labeled message to a topic ---
        self.stdout.write("\n🔍 Matching messages to topics...")
        messages_by_topic = {}  # topic_name -> [list of (text, label)]
        unmatched = 0

        for row in labeled_rows:
            text = row["text"]
            if len(text) < 10:
                continue  # skip too-short fragments

            # Stem the message words
            words = text.lower().split()
            stemmed_words = set(stemmer.stem(w) for w in words)

            # Find best matching topic by keyword overlap
            best_topic = None
            best_score = 0
            for topic_name, topic_kws in topic_stemmed.items():
                score = len(stemmed_words & topic_kws)
                if score > best_score:
                    best_score = score
                    best_topic = topic_name

            if best_topic and best_score >= 1:
                messages_by_topic.setdefault(best_topic, []).append(row)
            else:
                unmatched += 1

        total_matched = sum(len(v) for v in messages_by_topic.values())
        self.stdout.write(f"   ✅ Matched: {total_matched} messages")
        self.stdout.write(f"   ❌ Unmatched: {unmatched} messages (skipped)")
        self.stdout.write("   📊 Messages per topic:")
        for tname in sorted(messages_by_topic.keys()):
            count = len(messages_by_topic[tname])
            self.stdout.write(f"      {tname}: {count}")

        # --- 4. Generate individual client-therapist chats ---
        os.makedirs(output_dir, exist_ok=True)
        manifest = {"clients": {}, "admin_group": {}}
        random.seed(42)  # reproducible fixtures

        self.stdout.write("\n📝 Generating client-therapist chats...")
        for client_id, info in CLIENT_ASSIGNMENTS.items():
            # Gather messages for this client's assigned topics
            pool = []
            for topic_name in info["topics"]:
                pool.extend(messages_by_topic.get(topic_name, []))
            random.shuffle(pool)

            if len(pool) < messages_per_client:
                self.stdout.write(
                    self.style.WARNING(
                        f"   ⚠️  {info['parent']}: only {len(pool)} messages available "
                        f"(need {messages_per_client})"
                    )
                )

            selected = pool[:messages_per_client]
            parent_name = info["parent"]
            therapist_name = info["therapist"]

            # Generate timestamps: sessions over 4 weeks, 2-3 per week
            base_date = datetime(2026, 5, 4, 10, 0, 0)  # Mon May 4 2026
            lines = []
            session_day_offset = 0

            for i, row in enumerate(selected):
                # Every ~8 messages = new session (new day)
                if i > 0 and i % 8 == 0:
                    session_day_offset += 3  # 3 days between sessions

                # Parent messages therapy-relevant, therapist replies
                if i % 3 == 0:
                    # Therapist reply (positive/neutral guidance)
                    sender = therapist_name
                    # Pick a therapist-like message from neutral/positive pool
                    therapist_msgs = [m for m in pool if m["label"] in (1, 2)]
                    msg = random.choice(therapist_msgs)["text"] if therapist_msgs else "Noted, terima kasih."
                else:
                    # Parent message (use the labeled text directly)
                    sender = parent_name
                    msg = row["text"]

                # Time: spread within a 45-min session
                msg_time = base_date + timedelta(
                    days=session_day_offset,
                    minutes=i * 5,
                )
                ts = msg_time.strftime("[%d/%m/%Y, %H:%M:%S]")
                lines.append(f"{ts} {sender}: {msg}")

            filename = f"chat_client{client_id}.txt"
            filepath = os.path.join(output_dir, filename)
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            manifest["clients"][str(client_id)] = {
                "file": filename,
                "parent": parent_name,
                "child": info["child"],
                "therapist": therapist_name,
                "topics": info["topics"],
                "message_count": len(lines),
            }

            self.stdout.write(
                f"   ✅ {filename}: {len(lines)} messages "
                f"({parent_name} + {therapist_name})"
            )

        # --- 5. Generate admin group chat ---
        self.stdout.write("\n📝 Generating admin group chat...")
        group_pool = []
        for topic_msgs in messages_by_topic.values():
            group_pool.extend(topic_msgs)
        random.shuffle(group_pool)
        group_selected = group_pool[:group_size]

        # Use the 5 parents as senders in the group
        parent_names = [info["parent"] for info in CLIENT_ASSIGNMENTS.values()]
        admin_name = "Admin"

        base_date = datetime(2026, 6, 1, 9, 0, 0)
        lines = []
        for i, row in enumerate(group_selected):
            # Rotate senders: mostly parents, occasional admin reply
            if i % 7 == 6:
                sender = admin_name
                msg = "Terima kasih semua. Kami akan follow up dengan pihak terapi."
            else:
                sender = random.choice(parent_names)
                msg = row["text"]

            msg_time = base_date + timedelta(minutes=i * 15)
            ts = msg_time.strftime("[%d/%m/%Y, %H:%M:%S]")
            lines.append(f"{ts} {sender}: {msg}")

        filename = "chat_admin_group.txt"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        manifest["admin_group"] = {
            "file": filename,
            "senders": parent_names + [admin_name],
            "message_count": len(lines),
        }

        self.stdout.write(
            f"   ✅ {filename}: {len(lines)} messages "
            f"(5 parents + admin)"
        )

        # --- 6. Write manifest ---
        manifest_path = os.path.join(output_dir, "manifest.json")
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        self.stdout.write(f"\n📋 Manifest: {manifest_path}")

        # --- Summary ---
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ FIXTURE GENERATION COMPLETE"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"📁 Output directory: {output_dir}/")
        self.stdout.write(f"📊 Files generated: {len(CLIENT_ASSIGNMENTS) + 1}")
        self.stdout.write(f"📝 Total messages: {sum(len(v) for v in manifest['clients'].values()) + manifest['admin_group']['message_count']}")
        self.stdout.write("\n💡 Next steps:")
        self.stdout.write("   1. Upload individual chats:")
        for cid in CLIENT_ASSIGNMENTS:
            self.stdout.write(f"      python manage.py upload_chats --file fixtures/chat_client{cid}.txt --client-id {cid} --dry-run")
        self.stdout.write("   2. Then upload without --dry-run to save")
        self.stdout.write("   3. Train topic model: python manage.py train_topics")
        self.stdout.write("=" * 60)
