# 📚 Lesson Learned — Topic Modeling System

**Project:** Autism Center Chat Analyzer
**Date:** August 19, 2026

---

## 🧠 Lesson 1: Hybrid Topic Modeling Approach

### The Concept

There are two ways to do topic modeling:

| Approach | How it works | Problem |
|----------|-------------|---------|
| **Pure Unsupervised** | BERTopic finds clusters, names them from keywords | Topic names are messy ("makan - nasi - selera"), not user-friendly |
| **Pure Supervised** | You define topics manually, classify messages into them | Can't discover unexpected patterns, rigid |
| **Hybrid (ours)** | BERTopic finds clusters → maps to your 12 defined topics | Best of both worlds ✅ |

### The Pipeline

```
Messages (Malay/English mix)
    │
    ▼
BERTopic (unsupervised)
    │  → Embeddings (Sentence Transformers)
    │  → UMAP (dimensionality reduction: 384D → 5D)
    │  → HDBSCAN (clustering)
    │  → Extracted keywords per cluster
    │
    ▼
Topic Mapper (supervised mapping)
    │  → Compare BERTopic keywords vs defined topic keywords
    │  → Match to best-fitting defined topic
    │
    ▼
Database Output
    │  → Topic: "Eating Habits & Food Acceptance" 🍚
    │  → Keywords: [makan, nasi, selera]
    │  → Messages linked to topic
```

### Key Insight

> **BERTopic discovers the patterns. Your defined topics ensure relevance and consistency.**
> Without the mapping step, BERTopic gives you "makan - nasi - selera" as a topic name —
> not useful for therapists. The mapping gives them "Eating Habits & Food Acceptance".

---

## 🧠 Lesson 2: Separate Text Cleaners for Different Purposes

### The Problem

One cleaner can't serve both sentiment and topic modeling:

| Purpose | What to preserve | What to remove |
|---------|-------------------|----------------|
| **Sentiment** | Emotional words ("sangat", "gembira"), punctuation (!, ?) | Structural words only |
| **Topic Modeling** | Domain words only | All stopwords, greetings, names, fillers |

### The Solution — Dual Cleaning Pipeline

```
Raw Message: "anak sangat meraguk malam ni, saya risau 😢"
                    │
        ┌───────────┴───────────┐
        │                       │
   Light Clean              Aggressive Clean
   (for sentiment)          (for topic modeling)
        │                       │
  Keep: sangat,            Remove: sangat, risau,
  risau, meraguk, 😢        meraguk (emotional words)
        │                       │
  "sangat meraguk           "anak malam" ← only
   risau"                    domain words remain
        │                       │
        ▼                       ▼
  Sentiment: NEGATIVE     Topic: Sleep/Tantrum
  (emotional context      (thematic content
   preserved)              preserved)
```

### Why This Matters

If you use aggressive cleaning for sentiment:
```
"sangat risau" → removed → sentiment = NEUTRAL ❌ (wrong!)
```

If you use light cleaning for topic modeling:
```
"sangat risau" → kept → topic = "Parental Emotions" ← noise dilutes clusters
```

---

## 🧠 Lesson 3: UMAP — Dimensionality Reduction

### Why We Need It

Text embeddings = 384+ dimensions. HDBSCAN can't cluster in 384D (curse of dimensionality — all points look equidistant).

### What UMAP Does

```
384-dim embedding  →  UMAP  →  5-dim representation
                                 (preserves local + global structure)
                                      │
                                      ▼
                                 HDBSCAN clustering
                                 (now it works!)
```

### Key Parameters

| Parameter | What it does | Default |
|-----------|-------------|---------|
| `n_neighbors=15` | k-NN graph size (↑=global, ↓=local) | 15 |
| `n_components=5` | Target dimensions (↑=more info, ↓=faster) | 5 |
| `min_dist=0.0` | Min distance between points (0.0 = tight clusters) | 0.0 |
| `metric='cosine'` | Distance metric (cosine = good for text) | cosine |

### UMAP vs Alternatives

| Feature | UMAP | PCA | t-SNE |
|---------|------|-----|-------|
| Local structure | ✅ | ⚠️ | ✅ |
| Global structure | ✅ | ✅ | ❌ |
| Speed | ⚠️ | ✅ | ❌ |
| Good for clustering | ✅ | ⚠️ | ⚠️ |

---

## 🧠 Lesson 4: Django Management Commands

### What They Are

Instead of raw SQL:
```sql
INSERT INTO topic (name, keywords) VALUES ('Speech', '["bercakap"]');
```

We write Python commands:
```bash
python manage.py seed_topics
python manage.py train_topics
python manage.py clean_for_topic_modeling
```

### Why Use Them

- ✅ Python logic (loops, conditionals, error handling)
- ✅ Reusable (run anytime)
- ✅ Version-controlled (part of codebase)
- ✅ Can be scheduled (cron jobs)

### Key Methods

| Method | If exists | If doesn't exist |
|--------|-----------|------------------|
| `create()` | 💥 Error (duplicate) | ✅ Creates |
| `get_or_create()` | ✅ Returns existing | ✅ Creates (no update) |
| `update_or_create()` | ✅ Updates fields | ✅ Creates |

> **Lesson:** Always use `update_or_create()` for seeding data — it's idempotent (safe to run multiple times).

---

## 🧠 Lesson 5: Data Maintainability — Hardcoded vs Admin vs Dashboard

### The Problem

Hardcoded topics in Python:
```python
DEFINED_TOPICS = [...]  # Need to edit code to add topic
```

Bad: therapist says "add Toilet Training topic" → you have to edit code, commit, deploy.

### 3 Levels of Maintainability

| Level | Approach | Code Change Needed? | Who Updates |
|-------|----------|---------------------|-------------|
| **1. JSON file** | `data/topics.json` | ❌ (edit JSON) | Developer |
| **2. Django Admin** | `admin.py` registration | ❌ (admin UI) | Admin/Therapist |
| **3. Custom Dashboard** | Views + templates | ❌ (custom UI) | Any logged-in user |

### Best Practice: Bootstrap + Admin

```
Initial seed (one-time)           Ongoing maintenance
       │                                │
       ▼                                ▼
seed_topics.py                   Django Admin
(python manage.py seed_topics)   (localhost:8000/admin)
       │                                │
       ▼                                ▼
12 topics in DB                   Therapist adds new keywords
                                 (e.g., "meragam" → Tantrum topic)
                                 → no code changes
```

### Why Django Admin is Best for This Project

- ✅ Zero code changes to add/edit topics
- ✅ Therapists self-serve
- ✅ Audit trail (who changed what)
- ✅ 5 lines of code to set up
- ✅ Already built into Django

### admin.py Registration (5 lines)

```python
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "keywords")
```

### Viva Answer

> *"Initial topics are seeded via a management command for reproducibility. For ongoing maintenance, topics are managed through Django Admin — therapists can add keywords or new topics without code changes. This separates data management from application logic."*

---

## 🧠 Lesson 6: Language Strategy — English Names, Malay Keywords

### The Decision

| Field | Language | Why |
|-------|----------|-----|
| **Topic name** | English | Display label for therapists (clinical documentation standard) |
| **Keywords** | Malay | Matching against BERTopic output (conversations are in Malay) |

### Example

```python
{
    "name": "Eating Habits & Food Acceptance",        # English (display)
    "keywords": ["makan", "nasi", "bubur", "selera"],  # Malay (matching)
}
```

### Why This Works

- Users see: `Topic: Eating Habits & Food Acceptance 🍚` (clear, professional)
- BERTopic sees: `["makan", "nasi", "selera"]` → matches Topic keywords (Malay ↔ Malay)

### Viva Answer

> *"Topic names are display labels in English — standard for Malaysian clinical documentation. Keywords are in Malay because that's the language of the WhatsApp conversations. This separates presentation from computation."*

---

## 🧠 Lesson 7: Processing Order Matters

### Wrong Order (what I was tempted to do)

```
Upload conversations → Train BERTopic → Try to map → 💥 (Topic table empty!)
```

### Right Order (dependency chain)

```
1. Seed topics in DB (define 12 topics with keywords)
2. Upload conversations (dual cleaning runs automatically)
3. Train BERTopic (clusters form, maps to defined topics)
4. Run sentiment analysis
5. Dashboard shows results
```

### Why Order Matters

| Step | Depends on |
|------|------------|
| Upload conversations | Nothing (can run anytime) |
| Train BERTopic | Conversations must exist in DB |
| Topic mapping | Both BERTopic output AND defined topics must exist |
| Sentiment analysis | Conversations must be cleaned (sentiment) |

> **Lesson:** Always think about data dependencies before building a pipeline. Ask: "What does this step need to have been done first?"

---

## 🧠 Lesson 8: Malay Word Stemming — "cakap" vs "bercakap"

### The Problem

Malay uses prefixes that change word forms:

| Root word | With prefix | Meaning |
|-----------|-------------|---------|
| `cakap` | **ber**-cakap | to talk |
| `makan` | **di**-makan | being eaten |
| `tidur` | **ber**-tidur | sleeping |
| `main` | **ber**-main | playing |

So `cakap` and `bercakap` are the **same word**, different forms.

### What Happens Without Stemming

```
Message: "anak ni cakap dah banyak dah"
                    ↓
BERTopic extracts: "cakap"
                    ↓
Topic mapper checks: "Is 'cakap' in Speech keywords?"
                    ↓
Speech keywords: ["bercakap", "sebut", "perkataan"]
                    ↓
"cakap" ≠ "bercakap" → ❌ NO MATCH (but they're the same word!)
```

### The Solution: Sastrawi Stemmer

```python
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

stemmer = StemmerFactory().create_stemmer()

stemmer.stem("bercakap")  # → "cakap"
stemmer.stem("bermain")   # → "main"
stemmer.stem("di makan")  # → "makan"
```

### How It Works in Topic Mapping

```
BERTopic extracts: "bercakap"
        ↓
Stemmer: "bercakap" → "cakap"
        ↓
Compare against stemmed topic keywords:
Speech: ["cakap", "sebut", "perkataan"]  (also stemmed)
        ↓
Match! → Topic = Speech & Communication ✅
```

### 3 Levels of Matching

| Level | Approach | Example | Pros/Cons |
|-------|----------|---------|-----------|
| **1. Exact match** | `word in keywords` | "bercakap" ≠ "cakap" | ❌ Misses variants |
| **2. Stemming (Sastrawi)** | `stem(word) in stem(keywords)` | "cakap" = "cakap" | ✅ Handles all prefix variants |
| **3. Embeddings** | `cosine_similarity(word, keyword) > 0.85` | similarity = 0.94 | ✅ Handles synonyms + typos, but slower |

### Why Level 2 (Stemming) is Best for This Project

1. ✅ **Handles all Malay prefix variants** automatically (ber-, di-, ter-, pe-, men-, etc.)
2. ✅ **Well-known library** — good for viva (shows you know the Malay NLP ecosystem)
3. ✅ **Not too complex** — just one function call before matching
4. ✅ **Fast** — stemming is much faster than embedding similarity

### Installation

```bash
pip install Sastrawi
```

### Implementation in Topic Mapper

```python
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory

class TopicMapper:
    def __init__(self):
        self.stemmer = StemmerFactory().create_stemmer()

    def stem_word(self, word):
        return self.stemmer.stem(word.lower())

    def map_topic(self, bertopic_keywords, defined_topics):
        best_match = None
        best_score = 0

        for topic in defined_topics:
            # Stem the topic's keywords
            stemmed_topic_keywords = [self.stem_word(k) for k in topic["keywords"]]

            # Stem BERTopic keywords and count matches
            matches = 0
            for word in bertopic_keywords:
                stemmed_word = self.stem_word(word)
                if stemmed_word in stemmed_topic_keywords:
                    matches += 1

            score = matches / len(stemmed_topic_keywords)
            if score > best_score:
                best_match = topic
                best_score = score

        return best_match, best_score
```

### Viva Answer

> *"Malay uses prefixes (ber-, di-, ter-, pe-, men-) which create many word forms from one root. Using the Sastrawi stemmer, I reduce both BERTopic keywords and defined topic keywords to their root form before matching. This ensures 'cakap' matches 'bercakap' — they're the same word linguistically."*

---

## 📋 Commands Reference

### Setup
```bash
python manage.py makemigrations chat_analyzer
python manage.py migrate chat_analyzer
python manage.py seed_topics          # Seed 12 therapy topics
```

### Data Pipeline
```bash
python manage.py upload_chats --file=chat.txt --client-id=1
python manage.py clean_for_topic_modeling           # Backfill cleaning
python manage.py train_topics --verbose             # Train BERTopic
python manage.py analyze_sentiment                  # Run sentiment
```

### Testing
```bash
python manage.py test_cleaner          # Test text cleaning
python manage.py test_sentiment         # Test sentiment model
python manage.py check                 # Check Django config
```

---

## 🎯 Key Takeaways for AI Engineer Mindset

1. **Separate concerns** — different cleaning for different ML tasks
2. **Think about dependencies** — what needs to exist before this step?
3. **Design for maintainability** — will someone else be able to update this?
4. **Bootstrap + Admin** — seed initial data, let users manage ongoing changes
5. **Language strategy** — display language vs computation language can differ
6. **Understand your tools** — UMAP reduces dimensions, HDBSCAN clusters, BERTopic combines both
7. **Document your lessons** — future you will thank present you
8. **Handle language morphology** — Malay prefixes require stemming, not exact matching

---

*Authored by: nick (Future AI Engineer 🚀)*
*Project: Chat Analyzer — Therapy Conversation Analysis*
