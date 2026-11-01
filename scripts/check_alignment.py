"""
purpose: 
check_alignment.py as a drift detector: between db and Chroma corpus alignment check

liars = db - chroma ( rows say ready, chroma has no chunks )
ghosts = chroma - db ( chunks exist but no db row backs then )

"""
import sys
from pathlib import Path
from typing import Any, Optional
import django
from django.conf import settings

base_dir: Path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir))

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "finalyearengineredo.settings")
django.setup()

from chat_analyzer.models import TreatmentDocument
from chat_analyzer.services.rag_service import get_collection

def db_ready_titles() -> set[str]:
    """ Titles the DB claims are ingested: status: ready 
    QuerySet[str] -> set[str]
        
    """
    qs = (TreatmentDocument.objects
          .filter(status='ready', is_active=True)
          .values_list('title', flat=True))

    return set(qs)


def chroma_titles() -> tuple[set[str], int]:
    """
    distinct doc_titles present in chroma, plus count of malformed data 
    """
    col = get_collection() # we got collection returned from this rag_service method
    
    payload: dict[str, Any] = col.get(include=['metadatas'])

    metadatas: list[dict[str, Any]] = payload.get('metadatas', []) # [] if chroma didnt retunr metadata treat as empty list to handle from crashing

    titles: set[str] = set()
    malformed: int = 0

    for meta in metadatas:
        title: Optional[str] = meta.get('doc_title')
        if title is None:
            malformed += 1
        else:
            titles.add(title)
    return titles, malformed

def near_misses(a: set[str], b: set[str]) -> list[tuple[str, str]]:
    """ find out the case-insensitive collisions between the two diff sets.

    'ABA terapi' iin liars + 'aba terapi' in ghosts is really ONE bug
    # a string mismatch
    """
    lower_b: dict[str, str] = {t.lower(): t for t in b}
    return [(x, lower_b[x.lower()]) for x in a if x.lower() in lower_b]

def main() -> int:
    db_set: set[str] = db_ready_titles()
    chroma_set: set[str]
    malformed: int
    chroma_set, malformed = chroma_titles()

    liars: set[str] = db_set - chroma_set
    ghosts: set[str] = chroma_set - db_set

    print(f"DB (ready+active):    {len(db_set)} titles")
    print(f"Chroma (doc_title):   {len(chroma_set)} titles, {malformed} malformed metadata")

    print(f"TOTAL chunks in Chroma: {get_collection().count()}")
    print()

    if malformed:
        print(f"⚠ {malformed} chunks missing doc_title metadata")

    if not liars and not ghosts:
        print("✅ ALIGNED — disk-of-truth agrees: no liars, no ghosts.")
        return 0

    for t in sorted(liars):
        print(f"LIAR  (db claims ready, Chroma empty): {t!r}")
    for t in sorted(ghosts):
        print(f"GHOST (Chroma chunks, no db row):      {t!r}")

    for a, b in near_misses(liars, ghosts):
        print(f"↔ probable string mismatch: {a!r} vs {b!r}")

    return 1

if __name__ == "__main__":
    sys.exit(main())

