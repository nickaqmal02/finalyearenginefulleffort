"""Prove the blind-sheet -> original-label join resolves for both samples."""
import csv

SOURCE = "chat_analyzer/data/labeled_data/labeledsentimentdatatwo_balanced.csv"

# build the lookup: message_id (row position) -> original label
with open(SOURCE, newline="", encoding="utf-8") as f:
    original = {i: row["label"] for i, row in enumerate(csv.DictReader(f))}

print(f"source rows: {len(original)}")
print(f"label values present: {sorted(set(original.values()))}")

for path in ["eval/sample_150.csv", "eval/sample_100.csv"]:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    ids = [int(r["message_id"]) for r in rows]
    # every id must exist in source AND text must match (no off-by-one drift)
    joined = sum(1 for r in rows if int(r["message_id"]) in original)
    print(f"\n{path}: {len(rows)} rows, {joined} join to source")
    # spot-check: text in blind sheet == text in source at that position?
    with open(SOURCE, newline="", encoding="utf-8") as f:
        src_rows = list(csv.DictReader(f))
    mismatches = sum(1 for r in rows if src_rows[int(r["message_id"])]["text"] != r["text"])
    print(f"  text mismatches vs source: {mismatches} (must be 0)")
    # label distribution of the sample (via the join)
    from collections import Counter
    dist = Counter(original[int(r["message_id"])] for r in rows)
    print(f"  hidden label distribution: {dict(dist)}")
