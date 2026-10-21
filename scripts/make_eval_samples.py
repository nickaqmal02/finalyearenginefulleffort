"""Sample blind evaluation sets from the labeled sentiment dataset.

Usage: venv/bin/python scripts/make_eval_samples.py
Deterministic: seed=42 -> identical samples on every run.

Design decisions (viva material):
- message_id = row position (enumerate) in the source file. Stable as long
  as the source file is frozen (git-committed before sampling) — the ID is
  only a join key between blind sheets and rater responses, not a global PK.
- sample_150 (intra/inter-rater) and sample_100 (supervisor) are DISJOINT:
  supervisor reviews different messages, maximizing coverage of the 2k
  population. Trade-off: no 3-way comparison on shared messages, but the
  validity claim is about the dataset, not about individual messages.
- Blind sheets carry message_id + text ONLY. Annotators see exactly what
  the model saw (raw text), never the original label.
"""
import csv
import random

SOURCE = "chat_analyzer/data/labeled_data/labeledsentimentdatatwo_balanced.csv"
OUT_150 = "eval/sample_150.csv"
OUT_100 = "eval/sample_100.csv"


def main():
    # 1. Read population; assign message_id = row position
    with open(SOURCE, newline="", encoding="utf-8") as f:
        rows = [
            {"message_id": i, "text": row["text"], "label": row["label"]}
            for i, row in enumerate(csv.DictReader(f))
        ]
    print(f"Population loaded: {len(rows)} messages")

    # 2. Seed + disjoint sampling
    random.seed(42)
    sample_150 = random.sample(rows, 150)
    remaining = [r for r in rows if r not in sample_150]
    sample_100 = random.sample(remaining, 100)

    # 3. Write blind sheets (message_id, text only — NO label)
    for path, sample in [(OUT_150, sample_150), (OUT_100, sample_100)]:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["message_id", "text"])
            writer.writeheader()
            for r in sample:
                writer.writerow({"message_id": r["message_id"], "text": r["text"]})
        print(f"Wrote {path}: {len(sample)} rows")

    # 4. Sanity summary
    ids_150 = {r["message_id"] for r in sample_150}
    ids_100 = {r["message_id"] for r in sample_100}
    overlap = ids_150 & ids_100
    print(f"Overlap between sets: {len(overlap)} (expected 0 — disjoint by design)")
    print(f"Distinct messages covered: {len(ids_150 | ids_100)} / {len(rows)}")


if __name__ == "__main__":
    main()
