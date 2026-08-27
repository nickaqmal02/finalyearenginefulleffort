"""Read-only probe: stem every candidate keyword with the project's Sastrawi.
Purpose: build keyword lists where each entry is a DISTINCT stem (TopicMapper
stems both sides, so stem collisions are what count)."""
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

s = StemmerFactory().create_stemmer()

CURRENT = {
 "Speech": ["bercakap","sebut","perkataan","ayat","komunikasi","interaksi"],
 "Eating": ["makan","nasi","bubur","selera","makanan","daging","sayur"],
 "Tantrum": ["tantrum","mengamuk","merajuk","menangis","marah","melawan"],
 "Sleep": ["tidur","malam","lena","terjaga","buaian","rehat"],
 "Social": ["bergaul","bermain","berkawan","main","sosial","kawan"],
 "School": ["sekolah","cikgu","fokus","belajar","baca","tulis"],
 "Physical": ["gerak","motor","jalan","lompat","pegang","pijak","merangkak"],
 "TherapyProg": ["perubahan","terapi","berkembang","kemajuan","improvement"],
 "ParentEmo": ["risau","sedih","kecewa","stress","penat","gembira","syukur"],
 "Family": ["rumah","keluarga","ibu","ayah","kakak","abang"],
 "Sensory": ["sensory","rangsangan","fokus","perhatian","integrasi"],
 "Treatment": ["balut","urut","rawatan","sesi","balutan","urutan"],
}
CARD_ADD = {
 "Tantrum": ["amuk","tangis","sepak","baling","jerit","ganas","cry","angry","aggressive"],
 "Social": ["rakan","berkongsi","play","friend","share","group"],
 "Sleep": ["tido","bangun","siang","sleep"],
 "Eating": ["minum","suap","lauk","feed"],
 "TherapyProg": ["therapy","nampak","progress","baik","dapat"],
 "Treatment": ["sapu","kompres","latihan","teknik","kaedah","session","treatment"],
}

merged = {k: CURRENT.get(k, []) + CARD_ADD.get(k, []) for k in set(CURRENT) | set(CARD_ADD)}

stem_map = {}
for topic, words in merged.items():
    for w in words:
        st = s.stem(w.lower())
        stem_map.setdefault(st, []).append((topic, w))

print("=== CROSS-TOPIC STEM COLLISIONS (one word votes for 2+ topics) ===")
for st, uses in sorted(stem_map.items()):
    if len({t for t, _ in uses}) > 1:
        print(f"  '{st}' <- {uses}")

print("\n=== SAME-TOPIC REDUNDANCY (wasted slots: same stem twice) ===")
for st, uses in sorted(stem_map.items()):
    by_topic = {}
    for t, w in uses:
        by_topic.setdefault(t, []).append(w)
    for t, ws in by_topic.items():
        if len(ws) > 1:
            print(f"  {t}: {ws} -> '{st}'")

print("\n=== ENGLISH STEMS (does Sastrawi leave them untouched?) ===")
for w in ["therapy","tantrum","progress","session","treatment","cry","angry",
          "aggressive","play","friend","share","group","sleep","feed",
          "improvement","stress","sensory","motor"]:
    print(f"  {w!r:14} -> {s.stem(w)!r}")

print("\n=== KEY MALAY STEMS (what the cluster words collapse to) ===")
for w in ["menangis","mengamuk","merajuk","melawan","perubahan","kemajuan",
          "berkembang","balutan","urutan","rawatan","latihan","bermain",
          "berkawan","bergaul","berkongsi","makanan","terjaga","buaian",
          "nampak","dapat","tidur","tido","lena","masih","kena"]:
    print(f"  {w!r:14} -> {s.stem(w)!r}")
