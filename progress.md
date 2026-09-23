# progress.md — Chat Analyzer Engineering Journal

> The shared log of Nik + Hermes building this FYP together.
> Updated at the end of every work session. Newest entries at the **bottom**.
> Format: what we did → what Nik learned → what we went through → what's next.

---

## 2026-08-23 — soul.md locked in, DRF decision made, focus locked on topic modeling

### What we did today
- Reviewed full project state from history: hybrid topic pipeline is **code-complete and verified**
  (`topic_mapper.py` Sastrawi stemming + set-overlap matching wired into `topic_modeler.py`,
  two-tier mapping: Tier 1 → 12 defined topics, Tier 2 → discovered topics via `get_or_create`).
- Fixture data confirmed generated: `fixtures/chat_client10..14.txt` + `chat_admin_group.txt`
  (25 msgs each, sampled from 1,172 matched rows of `labeledsentimentdatatwo_balanced.csv`, seed=42 deterministic).
- Discussed next big skill: **DRF**. Nik already knows GET/POST views and FastAPI.
  Decision made: DRF is the right tool for THIS app (multi-user, role-based, ORM-heavy, admin-integrated)
  vs FastAPI (right for the BDA predictor: one model, no DB). Queued as the next module AFTER the
  topic-modeling milestone is closed.
- Locked working agreement into `~/.hermes/soul.md`: Nik's mentor-creed verbatim (prime directive:
  make Nik the best data scientist he can be — mentor, not code dispenser; rigor over shortcuts;
  he types, Hermes lights the way) + working logistics (hand-typing, verify everything, viva answers).
- Created this journal. From now on every session gets logged here — no exceptions.

### What Nik learned today
- **FastAPI vs DRF is a "right tool" decision, not a hype decision.** Structure/batteries/ORM/admin (DRF)
  vs speed/freedom/async (FastAPI). Being able to justify the choice = professional engineering.
- The value of a written working agreement: how a mentor-agent should teach is now explicit and enforceable.

### What we went through together
- Context recovery across a long project: reconstructed "where we are" from session history instead of
  guessing — a real-world skill (state is always messier than memory).
- Resisted scope creep: Nik asked about DRF (exciting!) and we consciously parked it to finish the
  topic-modeling milestone first. **Finish things, then start things.**

### What's next (in order)
1. Verify Nik's updated `whatsapp_parser.py` (he said he changed it — unverified).
2. End-to-end dry run: `python manage.py upload_chats --file fixtures/chat_client10.txt --client-id 10 --dry-run`
   → `--clean-only` → real upload.
3. `python manage.py train_topics` → inspect clusters → see which map Tier 1 vs Tier 2.
4. Tune `TopicMapper` threshold on real output.
5. THEN: DRF module (topics endpoint first).

### Open items carried from previous session
- Git push to origin/main **unconfirmed** (curl 55 last time). HEAD `a3e4910` + uncommitted changes
  (topic_mapper.py, topic_modeler.py, text_cleaner.py, admin.py, requirements.txt, generate_fixtures.py, fixtures/).
- Lesson 9 (lazy loading + py_compile) discussed but not yet appended to `LessonLearnFinal.md`.

## 2026-09-23 — Run 7: ID-pair plumbing kills the icontains lottery (topic pipeline COMPLETENESS closed)

### What we did today
- Diagnosed why 27/124 conversations had no topic after training. Root cause was TWO stacked bugs,
  both in the result→DB writeback, NOT in the mapper:
    1. `preprocess_messages` dedupes by exact text — duplicate texts trained once, so only one row
       per text could ever receive an assignment (11 rows).
    2. `save_topics_to_db` matched messages back to rows via `cleaned_text_topic__icontains=msg[:50].first()`
       — a substring lottery that picked unrelated rows containing the text as a substring
       (e.g. `icontains 'tidur'` matched 18 rows, picked id 2584 whose text is 'malam sempat ingat balut tidur').
  Decomposition of the 27 orphans: 14 both-causes, 11 dup-only, 2 substring-only, 0 unexplained.
- Run 7 fix (one variable): pass `(conversation_id, text)` pairs through the whole chain.
    - `train_topics` command builds `pairs = values_list("id", field_name)`
    - `train()` builds `text_to_ids: dict[text -> [ids]]`, trains on deduped keys, returns the map
    - `save_topics_to_db(..., text_to_ids=None)`: one `Conversation.objects.in_bulk(all_ids)` lookup
      (NOT wrapped in a comprehension — `in_bulk` already returns the dict; first re-run crashed on
      exactly this), decide `matches` once per text (cluster inheritance or outlier fallback),
      then EXPAND: every id sharing the text gets every matched topic. `unmapped_ids` + `rows_written`
      stats make silence impossible.
- Result: **124/124 covered, 0 uncovered, 0 conversations missing a primary.** Pipeline completeness
  milestone: CLOSED.

### What Nik learned today
- Data vs address: text is DATA (collides: duplicates, substrings); a PK is an ADDRESS. Joining on
  data where a key belongs = the entire class of bug. `icontains` join vs ID join = SQL joins on
  FK vs `WHERE name LIKE` — same principle.
- BERTopic contract: `fit_transform` accepts only `list[str]`, returns `(topics, probs)` positionally
  aligned to that list. Any reshaping (dedupe!) must happen outside and be carried as an explicit map.
- `fit_transform`/HDBSCAN assigns clusters; c-TF-IDF only NAMES them. Two different questions.
- `dict.get()` / `.discard()` / `get_or_create` = idempotence trio for re-runnable pipelines.
- Probe-first discipline: 5-second shell probe beat minutes-long full runs to locate the contract break;
  `AttributeError: 'tuple' object has no attribute 'strip'` was the predicted, then observed, crash.

### What we went through together
- Mentor bug of the day: Hermes' Edit-2 spec wrapped `in_bulk()` in a dict comprehension — double-wrap.
  `in_bulk` already returns `{id: obj}`; iterating a dict yields keys (ints) → `int has no attribute id`.
  Lesson: before wrapping a framework call, ask what it already returns.
- Run 7 exposed the NEXT problem cleanly: assignment QUALITY. Therapy Progress = 120/124 rows,
  Sensory = 116, 100/103 texts multi-topic, only 2 clusters (72+22), 9 outliers, and the literal
  word 'tidur' inherited Therapy Progress (via cluster 0 inheritance: HDBSCAN blobbed the short texts)
  while Sleep Patterns sits at 0. Deliberately NOT touched: one variable per run.

### What's next (in order)
1. **Run 8 (quality):** seed keyword de-overlap (generic words: kurang/berhenti/sayang/bermain/rasa...),
   primary-election logic, maybe IDF-weighted scoring. Receipts now exist (distribution above).
2. Wire `analyze_new_messages` (transform-only path) to a command — no full retrain per upload.
3. ClientTopicScore / TopicTrend computation (both tables at 0 rows).
4. Parked: TypedDict `TopicMatch` across the 3 match-producers; mypy CI; type annotations on touched signatures.

