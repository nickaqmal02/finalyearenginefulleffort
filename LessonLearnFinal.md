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

## 🧠 Lesson 9: Transformer Mechanics — the model under every component we use

**Date:** October 31, 2026

Everything in this project touches a Transformer: XLM-R encodes sentiment, BERTopic's
sentence-transformer embeddings are Transformers, and the interview chatbot is a decoder
LLM. Not being able to explain the mechanism = using tools you can't defend.

### 9.1 Where a language model sits

```
Artificial Intelligence
└── Machine Learning          learns from data, not hardcoded rules
    └── Deep Learning         multi-layer neural networks
        └── Neural Language Model    objective = predict text
            └── Large Language Model  same objective, scaled past emergence thresholds
```

- Not all ML is language modeling: vision (CNN/ViT), tabular (XGBoost), clustering (HDBSCAN).
- BERTopic is ML (UMAP + HDBSCAN) but **not** a language model. Sastrawi is rule-based, **not ML**.
- XLM-R is a language model but **not large**. GLM-5.2 is a language model **and** large.

### 9.2 Two phases, two different supervision regimes

| Phase | Who | Objective | Supervision |
|---|---|---|---|
| Pre-training | Meta (XLM-R), OpenAI (GPT) | masked LM / next-token | **self-supervised** — labels generated from the text itself |
| Fine-tuning | me (Sentiri) | sentiment classification | **supervised** — human-annotated labels |
| Inference | deployed API | none | none — forward pass only |

Self-supervised ≠ supervised fine-tuning. They are sequential phases of the same model.
The viva-safe sentence: *"XLM-R was self-supervised during pre-training; I supervised-fine-tuned
it on labelled sentiment data."*

### 9.3 Masked vs autoregressive

| | Masked (BERT, XLM-R) | Autoregressive (GPT, GLM) |
|---|---|---|
| Learns | fill the blank from BOTH sides | predict the NEXT token from the left |
| Architecture | encoder | decoder |
| Good at | understanding: classification, embeddings, analysis | generation: chat, code, summarisation |
| Our use | Sentiri sentiment | interview chatbot / GLM-5.2 |

Not two architectures invented separately — the same block with one line of difference:
the decoder masks future positions to −∞ so a token can only see the past.

### 9.4 The one formula

```
Attention(Q, K, V) = softmax( QKᵀ / √d_k ) · V
```

- `Q = X·Wq` — what this token is looking for
- `K = X·Wk` — what each token offers
- `V = X·Wv` — the actual content each token gives
- `QKᵀ` — every token dotted against every token → relevance scores
- `√d_k` — scaling; without it, high-dimensional dot products saturate the softmax
- `softmax` — per-row percentages summing to 1
- `·V` — weighted blend of contents

**No selection happens.** Attention is a weighted mixture, not a nearest-neighbour lookup.
This was the hardest mislearn to shake: RAG *selects* the closest document; attention *blends*
all of them, proportionally.

Full stack, four lines:

```
X₀ = Embed(tokens) + PosEnc
X_l = LayerNorm(X + MultiHead(X)); LayerNorm(X + FFN(X))   for l = 1..L
p  = softmax(X_L · W_out)
ŷ ~ p → append → repeat until [EOS] or max_tokens
```

### 9.5 Parameters vs activations — the master key

| Parameters (frozen) | Activations (per input) |
|---|---|
| embedding table | Q, K, V |
| Wq, Wk, Wv, Wo | attention percentages |
| FFN weights, LayerNorm γ/β | context vectors |
| output matrix | output logits / probabilities |
| learned in training, stored on disk | computed during every forward pass, discarded |
| identical for every user and query | unique to this input |

Every "does it change?" question collapses into: *which of these two do you mean?*

- Embeddings: **fixed lookup** — "chocolate" always starts from the same vector.
- Context vector: **fresh blend** — different in every sentence, recomputed per layer and per pass.
- Weights: **never change at inference** — backprop and weight updates are training-only.
- Softmax: **runs always** — it is part of the forward pass, in both training and inference.

### 9.6 How an answer is actually generated

```
"what is chocolate ?" → tokens → embeddings → 12 layers → final vector of "?"
→ × output matrix → 50,000 scores → softmax → sample/argmax → "Chocolate"
→ append → recompute everything → "is" → append → … → [EOS] → stop
```

- The output layer is the same dot-product matching as attention, one last time:
  final vector vs every vocabulary column → "which known word am I closest to?"
  (often weight-tied to the embedding table).
- **[EOS] is a learned stop**, not built-in logic: every SFT training answer ended with it,
  so complete answers make [EOS] win. Badly tuned models ramble — proof that stopping is a skill.
- **Causal masking** means earlier tokens never see appended ones → their activations never change
  during generation → which is exactly why KV caching is valid.
- Encoders are the opposite: bidirectional attention means changing one token reshuffles every
  context vector — better understanding, impossible generation.

### 9.7 Consequences that show up in production

- **Statelessness:** every API call recomputes from scratch; nothing persists between tweets.
- **Chat "memory" is not memory:** conversation history is re-pasted into the input each turn,
  and attention blends it fresh. Past the context window, early turns are dropped — that's the
  model "forgetting."
- **Same question, different answer:** context vectors are deterministic, but token *selection*
  can sample from the distribution (temperature). Deterministic activations ≠ deterministic output.
- **Data quality beats raw scale for a narrow task:** fine-tuned 270M XLM-R on clean domain data
  beats a prompted trillion-parameter model on sentiment. But instruction-following and in-context
  learning are emergent at scale and can't be bought with cleaner data on a small model.

### 9.8 Why this matters for the reranker story

The cross-encoder reranker degraded retrieval (hit@5 1.00 → 0.64) not because attention was
broken but because its **learned attention percentages over-weighted lexical overlap** between
query and document tokens — inflating keyword-matching documents and demoting semantically
relevant ones. Being able to explain the failure in terms of the mechanism, not just the metric
drop, is the difference between reporting a result and understanding a system.

### Viva answer

> *"A Transformer is a stack of self-attention layers where each token computes Query, Key and
> Value vectors from a fixed embedding table, scores itself against every other token by dot
> product, converts those scores to blend proportions with softmax, and absorbs a weighted
> combination of the Values — producing a context vector that is recomputed for every input.
> The parameters doing this are frozen after training; only the activations change per query.
> XLM-R stacks twelve such encoder layers and feeds the [CLS] token's final context vector into
> my sentiment classification head, which I fine-tuned. The only difference between XLM-R and a
> GPT-style decoder is a causal mask that hides future tokens — which is what makes generation
> possible and understanding weaker."*

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
