"""Inspect the Chroma treatment_documents collection + TreatmentDocument rows.

Boilerplate inspection script (config-tier). Answers: which docs are indexed,
chunk counts per doc, and whether the .md files are in the collection.
"""
import sqlite3
from pathlib import Path

BASE = Path("/Users/apple/degree/finalyearengineredo")
CHROMA_DIR = BASE / "data" / "vector_store"

# --- Chroma side ---
import chromadb

client: chromadb.ClientAPI = chromadb.PersistentClient(path=str(CHROMA_DIR))
try:
    col = client.get_collection("treatment_documents")
except Exception as exc:
    print("Chroma ERR:", exc)
    col = None

if col is not None:
    data = col.get(include=["metadatas", "documents"])
    titles: dict[str, int] = {}
    for meta in data["metadatas"]:
        title = meta.get("doc_title", meta.get("source", "?"))
        titles[title] = titles.get(title, 0) + 1
    print("=== Chroma: chunks per doc ===")
    for title, count in sorted(titles.items()):
        print(f"  {title}: {count} chunks")
    print(f"  TOTAL: {len(data['ids'])} chunks")
    print()
    print("=== Sample chunk (id + first 120 chars) ===")
    for cid, doc in list(zip(data["ids"], data["documents"]))[:3]:
        print(f"  [{cid}] {doc[:120]!r}")

# --- Django side ---
print()
print("=== SQLite: treatment document rows ===")
con = sqlite3.connect(BASE / "db.sqlite3")
cur = con.cursor()
cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%eatment%'"
)
tables = [r[0] for r in cur.fetchall()]
print("tables found:", tables)
for table in tables:
    cur.execute(f"SELECT * FROM {table} LIMIT 10")
    cols = [d[0] for d in cur.description]
    for row in cur.fetchall():
        print(f"  {dict(zip(cols, row))}")
