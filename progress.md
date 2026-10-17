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

## 2026-09-23 — Run 8: Topic QUALITY (8a seed de-overlap + 8b primary election + 8c coverage override)

### What we did today (3 sub-runs, each one variable)
- **8a — Seed de-overlap:** Audited all 12 seed keyword lists. Found 11 stems owned by >1 topic (main in 4 lists,
  sayang/menangis/rasa/gembira/syukur/fokus/cerita/interaksi/sesi/raung each in 2). For each: domain ruling on which
  topic keeps it (sayang→Sensory, main→Physical, gembira+syukur→Parental, fokus→School, cerita→Social, interaksi→Speech,
  sesi→Treatment, raung→Tantrum). Therapy Progress gutted of all evaluators (bagus/makin/terus/improve/hasil/kurang/
  tahniah/perubahan) — kept only therapy-specifics (perkembangan/fasa/konsisten/terapi/maju/proses). Result: 0 collisions.
- **8b — Primary election fix:** `map_cluster_with_alternatives` retired the `min_gap` requirement. Gap was calibrated
  for greedy seeds (Therapy 3.5 vs Sensory 2.0 = gap 1.5). After 8a balanced scores (Therapy 2.5 vs Sensory 2.0 = gap
  0.5 < 1.0), 115/124 rows lost their primary. Retiring gap restored 123/124 primaries.
- **8c — Full-coverage override (Door 1):** For each deduped text, stem all tokens and check if exactly ONE topic
  covers ALL of them (`hits == len(tokens) and hits > 0 → coverage[topic] = hits; if len(coverage) == 1 → override`).
  Fires before cluster inheritance (Door 2) and outlier fallback (Door 3). Override writes primary=True, confidence=0.9.

### Results — verified from DB
- covered: 123/124 | primaries: 123 | no_primary: 0
- Sleep Patterns: 0 → **6** (3× 'tidur' + 'malam tidur' + 2 more) ← THE GOAL
- Parental Emotions: 0 → **8** (syukur, gembira) ← BONUS
- Physical Development: 25 → **28** (kerja jalan) ← BONUS
- Treatment Methods: 1 → **4** (sesi) ← BONUS
- Sensory: 116 → **92** | Therapy: 116 → **92** ← de-overlap reduced greedy swallowing
- Probe: [2482] 'tidur' → Sleep(primary=True) ✅ | [2483] 'malam tidur' → Sleep(primary=True) ✅
- Commit: aa40d11, pushed to origin/main

### What Nik learned
- Three-door architecture: (1) coverage override [supervised, unambiguous msgs],
  (2) cluster inheritance [unsupervised HDBSCAN + supervised cluster→topic mapping],
  (3) outlier fallback [supervised direct keyword match]. Each door has an exit condition;
  only Door 1 overrides — Doors 2+3 defer to the cluster or direct mapping.
- HDBSCAN + c-TF-IDF serve the ~88 ambiguous messages whose words span multiple topics;
  coverage handles the ~15 unambiguous ones with zero ML compute. Hybrid = both, not either/or.
- Threshold recalibration: a threshold tuned for one distribution (greedy seeds) breaks on another (de-overlapped).
  `min_gap=1.0` assumed Therapy would dominate; when 8a balanced scores, the gap died everywhere.
- `> 1` vs `== 1`: one character bug that fired the override on TIES instead of unambiguous matches.
  Simulation proved the design worked; the bug was in the condition, not the logic.

### What's next
1. **MVP build:** DRF API layer (topics/conversations/messages endpoints, serializers, role-based permissions).
   Django templates + Chart.js for dashboard — API-first so React can consume later.
2. Parked (post-MVP): transform-only path (analyze_new_messages), ClientTopicScore/TopicTrend,
   HDBSCAN tuning (blob → more clusters), TypedDict TopicMatch + mypy CI.


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
2. Parked: TypedDict `TopicMatch` across the 3 match-producers; mypy CI; type annotations on touched signatures.

---

## 2026-10-06 — Policy C step 1: ClientTopicScore guard against discovered topics (verification deferred)

### What we did today
- Reviewed `signals.py` `update_client_topic_score_on_save`: post_save on MessageTopic → recompute (client, topic) pair via `aggregate(Avg, Count)` → `ClientTopicScore.objects.update_or_create(...)`. Single listener handles every save scenario.
- Taught signals concept: Django's pub/sub mechanism (`@receiver(post_save, sender=...)`); `instance` = the saved object; `created` = INSERT vs UPDATE. Analogy: `addEventListener` for the database.
- Taught `.aggregate()` semantics: returns ONLY the dict of names you declared (e.g. `{'avg_score': 0.75, 'msg_count': 4}`). `client_id` / `topic_id` come from `conv.client_id` and `instance.topic_id` separately — the filter inputs, not the aggregate output.
- **Nik's instinct caught the real bug:** the existing signal was including `discovered` topics in the aggregate. Result: dashboard showed aggregates for topics the admin hadn't promoted to `active` yet. Two policies considered:
  - A — exclude discovered in the aggregate filter (simple)
  - B — compute including discovered, filter at display time
  - **C — A + a SECOND signal on Topic.post_save to recompute when admin promotes discovered → active** (most correct)
- Nik picked C; reasoning: aggregate must stay in sync on the promotion event itself, since no MessageTopic gets saved in that scenario.

### Policy C Step 1 implementation (today)
- Added `topic__status='active'` to the MessageTopic filter clause (filters discovered/archived at source).
- Added explicit guard: `if instance.topic.status != 'active': return` before `update_or_create` — semantically tied to Policy C's "approved topics only" rule.
- Selected Option 1b-B (check topic status directly) over 1b-A (skip on empty filter) because: explicit policy statement beats incidental empty-set detection. Both are functionally identical when topic is discovered.
- Reasoning for 1b-B: "avoid zero-noise rows" — keep `ClientTopicScore` meaningful; dashboard view doesn't have to filter out empties.

### What Nik learned
- **The 0.0 score mystery decoded:** Ravi Kumar's "Sleep and Routine" ClientTopicScore = 0.0 was NOT a bug. Live diagnostic:
      Raw (score, is_primary): [(1.0, False), (1.0, False), ...]  ← 11 rows, ALL is_primary=False
      Stored CTS: 0.0
      Ravi's primary topics: ['Progress and Sessions', 'buka-nangis-baru', 'Speech and Emotional Feedback', 'Behaviour and Transitions', 'menangis tidur-mampu-suka bagus', ...]
    Sleep scores 1.0 but never wins primary election (Progress/Speech/Behaviour dominate). Filter `is_primary=True` → 0 rows → aggregate NULL → `or 0.0` → 0.0. **Check 1 lesson in production.**
- Signals are reactive, not active: a signal fires on save; you don't "take the next topic." Each save pins one (client, topic) pair and recomputes just that pair.
- `pre_save` + `post_save` share state via the same Python object reference. Setting `instance._old_status = ...` in `pre_save` persists into `post_save` because it's an attribute on the in-memory object — both signals receive the same reference.
- Two valid decisions for "detect topic promotion": (A) always recompute on Topic.post_save (simple, idempotent, wasteful on description edits), (B) only recompute on `discovered → active` transition (efficient, needs old-state capture via pre_save). Nik picked B.
- Test-fixture hygiene lesson: `aggregate(Avg)` over zero rows returns NULL, NOT an exception. `or 0.0` is null-coalescing, not exception handling. Test runs must clean both ClientTopicScore AND MessageTopic rows for the test pair (unique_together on (conversation, topic) bites if you only clean one).

### What we went through together
- Nik dodged three open viva questions in a row (the `or 0.0` guard, the discovered→active transition gap, the `instance._old_status` mechanism) — needed firm re-asking each time. Reinforced: dodging = plausible output with no understanding behind it.
- Hit `UNIQUE constraint failed: chat_analyzer_messagetopic.conversation_id, chat_analyzer_messagetopic.topic_id` mid-test. Diagnosis: leftover MessageTopic row from prior test run — only ClientTopicScore was being deleted. Test fixture leak between runs is now a known smell in this codebase.
- **Verification deferred (Path B):** Nik chose to move forward without running the live 7-print guard test. Reasoning accepted, logged here as a known-unverified step. **Risk:** if Signal 1's `if instance.topic.status != 'active': return` has a typo or is in the wrong function, it won't actually skip discovered-topic saves, and zero-noise rows will keep appearing on promotion. Bug-hunt is on Nik, not on us.
- Surfaced two production smells (not bugs, not fixing today):
  1. `is_primary` election: Sleep scores 1.0 but never wins primary. Model behavior — modeler needs review.
  2. Topic name quality: discovered topics like `buka-nangis-baru` and `menangis tidur-mampu-suka bagus` (three unrelated words jammed together) signal seed keyword overlap. Run 8 thread continues.

### What's next (Policy C step 2)
1. **Signal 2 on Topic.post_save:** `pre_save` captures `_old_status`; `post_save` detects `discovered → active` transition; recomputes ClientTopicScore for ALL clients with MessageTopics for that topic (loop over `conversation__client_id` distinct values).
2. (After) wire `analyze_new_messages` (transform-only path).
3. (After) DRF API endpoints: topics, conversations, messages — role-based permissions.
4. **Viva sweep (unpaid):** revisit signal guard `if instance.topic.status != 'active': return` and run the live 7-print test before demo day.

---

## 2026-10-06 (late session) — Recompute trigger inside `train_topics` command — VERIFIED ✅

### What we did
- Decision path: abandoned the `Topic.post_save` signal (Policy C step 2) in favour of recomputing inside `train_topics` after `train_topics()` returns. Reasoning: the **actual event** that changes MessageTopic scores is `train_topics`, not any Topic.save(). The signal was chasing the wrong trigger. The command knows exactly when the data has settled.
- Modified `chat_analyzer/management/commands/train_topics.py`:
  - Added `Avg, Count` to the existing `django.db.models` import
  - Added recompute block inside `if result:` (after `train_topics()` returns, before "Show discovered topics"):
    - distinct (client_id, topic_id) tuples where `is_primary=True` AND `topic__status='active'`
    - per-pair aggregate → `ClientTopicScore.objects.update_or_create(...)` with `or 0.0` / `or 0` guards
    - end-count print: `✅ Recalculated N client-topic pair(s)`
- Verified live: `python manage.py train_topics --clean-first --limit 10 --verbose` runs and prints:
  ```
  ✅ Topic modeling complete!
  📊 Recalculating ClientTopicScore aggregates...
  ✅ Recalculated 42 client-topic pair(s)
  ```

### What Nik learned
- **The right trigger is the command, not the signal.** Signals are for fine-grained model events; commands are for orchestrated workflows. The retrain *is* an orchestrated workflow — it cleans, trains, writes MessageTopic rows. Recompute belongs at its tail.
- **Bulk_create and signals:** `bulk_create` does NOT fire `post_save`. The earlier reasoning about "bulk saves bypass signals" is why even if Signal 1 were perfectly tuned, recompute inside the command is more reliable than relying on signal chaining.

### What we went through together
- Hit decision fatigue end-of-session. Nik tried to bail with "i wanna give up" — pulled back: deliverables already 90% done. Two valid closure paths were offered, Nik picked option that fit his state.
- Persisted question raised at session end (non-primary topics should also count) — parked. It's a real design question but **not for tonight**. Defer to next session.

### What's next
1. **Discovered-topic quality (Run 8 thread, URGENT for demo):** 3 of 9 discovered topics are garbage:
   - `buka-nangis-baru` (3 unrelated words in name)
   - `child-has-the` (English stopwords leaking — `child`, `has`, `the` — cleaner is not stripping English tokens)
   - `menangis tidur-mampu-suka bagus` (3 unrelated words, same jammed pattern as `buka-nangis-baru`)
   - These come from seed keyword overlap and short-text cluster inheritance. Run 8 8a/8b/8c work continues here.
2. **Viva sweep (unpaid):** run the 7-print live test for Signal 1's `if instance.topic.status != 'active': return` guard before demo day. **Path B is currently a known-unverified risk.**
3. DRF API endpoints (post-Run 8).
4. Parked: `is_primary` election behaviour (Sleep never wins primary despite scoring 1.0); non-primary topic scoring decision (asked, deferred).

---

## 2026-10-06 — Policy C step 1: ClientTopicScore guard against discovered topics (verification deferred)

### What we did today
- Reviewed `signals.py` `update_client_topic_score_on_save`: post_save on MessageTopic → recompute (client, topic) pair via `aggregate(Avg, Count)` → `ClientTopicScore.objects.update_or_create(...)`. Single listener handles every save scenario.
- Taught signals concept: Django's pub/sub mechanism (`@receiver(post_save, sender=...)`); `instance` = the saved object; `created` = INSERT vs UPDATE. Analogy: `addEventListener` for the database.
- Taught `.aggregate()` semantics: returns ONLY the dict of names you declared (e.g. `{'avg_score': 0.75, 'msg_count': 4}`). `client_id` / `topic_id` come from `conv.client_id` and `instance.topic_id` separately — the filter inputs, not the aggregate output.
- **Nik's instinct caught the real bug:** the existing signal was including `discovered` topics in the aggregate. Result: dashboard showed aggregates for topics the admin hadn't promoted to `active` yet. Two policies considered:
  - A — exclude discovered in the aggregate filter (simple)
  - B — compute including discovered, filter at display time
  - **C — A + a SECOND signal on Topic.post_save to recompute when admin promotes discovered → active** (most correct)
- Nik picked C; reasoning: aggregate must stay in sync on the promotion event itself, since no MessageTopic gets saved in that scenario.

### Policy C Step 1 implementation (today)
- Added `topic__status='active'` to the MessageTopic filter clause (filters discovered/archived at source).
- Added explicit guard: `if instance.topic.status != 'active': return` before `update_or_create` — semantically tied to Policy C's "approved topics only" rule.
- Selected Option 1b-B (check topic status directly) over 1b-A (skip on empty filter) because: explicit policy statement beats incidental empty-set detection. Both are functionally identical when topic is discovered.
- Reasoning for 1b-B: "avoid zero-noise rows" — keep `ClientTopicScore` meaningful; dashboard view doesn't have to filter out empties.

### What Nik learned
- **The 0.0 score mystery decoded:** Ravi Kumar's "Sleep and Routine" ClientTopicScore = 0.0 was NOT a bug. Live diagnostic:
      Raw (score, is_primary): [(1.0, False), (1.0, False), ...]  ← 11 rows, ALL is_primary=False
      Stored CTS: 0.0
      Ravi's primary topics: ['Progress and Sessions', 'buka-nangis-baru', 'Speech and Emotional Feedback', 'Behaviour and Transitions', 'menangis tidur-mampu-suka bagus', ...]
    Sleep scores 1.0 but never wins primary election (Progress/Speech/Behaviour dominate). Filter `is_primary=True` → 0 rows → aggregate NULL → `or 0.0` → 0.0. **Check 1 lesson in production.**
- Signals are reactive, not active: a signal fires on save; you don't "take the next topic." Each save pins one (client, topic) pair and recomputes just that pair.
- `pre_save` + `post_save` share state via the same Python object reference. Setting `instance._old_status = ...` in `pre_save` persists into `post_save` because it's an attribute on the in-memory object — both signals receive the same reference.
- Two valid decisions for "detect topic promotion": (A) always recompute on Topic.post_save (simple, idempotent, wasteful on description edits), (B) only recompute on `discovered → active` transition (efficient, needs old-state capture via pre_save). Nik picked B.
- Test-fixture hygiene lesson: `aggregate(Avg)` over zero rows returns NULL, NOT an exception. `or 0.0` is null-coalescing, not exception handling. Test runs must clean both ClientTopicScore AND MessageTopic rows for the test pair (unique_together on (conversation, topic) bites if you only clean one).

### What we went through together
- Nik dodged three open viva questions in a row (the `or 0.0` guard, the discovered→active transition gap, the `instance._old_status` mechanism) — needed firm re-asking each time. Reinforced: dodging = plausible output with no understanding behind it.
- Hit `UNIQUE constraint failed: chat_analyzer_messagetopic.conversation_id, chat_analyzer_messagetopic.topic_id` mid-test. Diagnosis: leftover MessageTopic row from prior test run — only ClientTopicScore was being deleted. Test fixture leak between runs is now a known smell in this codebase.
- **Verification deferred (Path B):** Nik chose to move forward without running the live 7-print guard test. Reasoning accepted, logged here as a known-unverified step. **Risk:** if Signal 1's `if instance.topic.status != 'active': return` has a typo or is in the wrong function, it won't actually skip discovered-topic saves, and zero-noise rows will keep appearing on promotion. Bug-hunt is on Nik, not on us.
- Surfaced two production smells (not bugs, not fixing today):
  1. `is_primary` election: Sleep scores 1.0 but never wins primary. Model behavior — modeler needs review.
  2. Topic name quality: discovered topics like `buka-nangis-baru` and `menangis tidur-mampu-suka bagus` (three unrelated words jammed together) signal seed keyword overlap. Run 8 thread continues.

### What's next (Policy C step 2)
1. **Signal 2 on Topic.post_save:** `pre_save` captures `_old_status`; `post_save` detects `discovered → active` transition; recomputes ClientTopicScore for ALL clients with MessageTopics for that topic (loop over `conversation__client_id` distinct values).
2. (After) wire `analyze_new_messages` (transform-only path).
3. (After) DRF API endpoints: topics, conversations, messages — role-based permissions.
4. **Viva sweep (unpaid):** revisit signal guard `if instance.topic.status != 'active': return` and run the live 7-print test before demo day.



## 2026-10-06 (after Deloitte submit) — Internship application submitted, build plan locked

### What we did today
- Filled Deloitte AI&Data internship application form. Skill list submitted:
  `Python - Expert, Django - Advanced, SQL - Intermediate, Machine Learning - Intermediate, NLP - Intermediate, RAG - Intermediate, Jupyter - Intermediate, Quarto - Intermediate`
  (193 chars, all skills backed by repo evidence)
- Discussed and rejected overclaiming: React/FastAPI/DRF all readme-badged but NOT yet implemented in repos.
  Decision: don't put them on the form. Build them in the 4-month runway (Oct 2026 → Jan-Mar 2027).
- Discussed the actual rejection sensitivity. Re-application is normal and supported.
  Most Big 4 firms give feedback. Build pipeline → reapply stronger.

### What's next (4-month build plan for reapplication strength)
1. **DRF in Sentiri** (2 weeks) — serializers, 4-5 endpoints, role-based permissions.
   Unblocks: update README badges honestly.
2. **FastAPI microservice** (2 weeks) — standalone service consuming Sentiri via DRF.
   Unblocks: AI/ML Engineer positioning, microservice architecture.
3. **Quarto polish** (1 week) — convert RAG_notebook.qmd into a portfolio piece, publish.
   Unblocks: data-science narrative strength.
4. **React dashboard widget** (4 weeks, last) — only if everything else is solid.
   Unblocks: full-stack claim credibility.

### Open items (unchanged)
- Run 8 garbage-topic cleanup (`buka-nangis-baru`, `child-has-the`, `menangis tidur-mampu-suka bagus`)
- DRF endpoints (above)
- FastAPI service (above)
- Viva sweep: run 7-print live test for Signal 1 guard before demo day.
- Fix broken LinkedIn link in README (`yourusername` placeholder → real URL).

---

## 2026-10-06 (evening session) — DiagnosisDocument FileField swap + custom upload view + glassmorphism UI

### What we did
- **DiagnosisDocument model swap:** Replaced `file_path` (CharField), `file_name` (CharField), `file_size` (IntegerField) with a single `FileField(upload_to='diagnosis_documents/%Y/%m/', validators=[FileExtensionValidator(['pdf', 'docx', 'png', 'jpg', 'jpeg'])])`. Migration applied. Uploads land at `MEDIA_ROOT/diagnosis_documents/<YYYY>/<MM>/<filename>`.
- **Admin UX:** Switched `DiagnosisDocumentAdmin` from `raw_id_fields` to `autocomplete_fields` for `client`, `uploaded_by`, `approved_by`. Clean type-to-search, no popup icons.
- **Custom upload view (5-layer pattern taught):** Built `UploadDocumentView` mirroring the existing `UploadChatsView` pattern:
  1. **Form** (`UploadDocumentForm` in forms.py): client, file, document_type fields. `__init__` sets up crispy `FormHelper` with `Layout`, `Fieldset`, `Submit`, `Button`.
  2. **View** (`UploadDocumentView` in admin.py): GET renders empty form; POST validates → `DiagnosisDocument.objects.create(client=..., file=..., document_type=..., uploaded_by=request.user)` → success message → redirect to changelist.
  3. **Template** (`upload_document.html`): `enctype="multipart/form-data"`, `{% crispy form form.helper "unfold_crispy" %}`.
  4. **URL** (`DiagnosisDocumentAdmin.get_urls()`): `path('upload-document/', self.admin_site.admin_view(UploadDocumentView.as_view()), name='chat_analyzer_diagnosisdocument_upload')`.
  5. **Button** (`change_list.html` override + `change_list_template` class attr): frosted glass pill link on changelist.
- **Verified end-to-end:** Admin clicks "Upload Diagnosis Document" → form renders → selects client + PDF → uploads → success message → file lands in `media/diagnosis_documents/2026/10/`. ✅
- **Glassmorphism UI attempt:** Tried Tailwind CDN for Apple-style frosted glass pill buttons on changelist + form submit. Hit three bugs:
  1. **Missing `margin:` keyword** in template div style (`20px auto` → `margin: 20px auto`).
  2. **`render_template` context bugs:** `has_change_permisssion` (3 s's typo) + `has_permission: False` (overrode `each_context`'s correct `True`). Killed breadcrumbs. Fixed both.
  3. **Tailwind CDN conflicted with unfold's built-in Tailwind** — submit button text invisible, padding broken, hover dead. Root cause: unfold ships its own compiled Tailwind CSS; loading the CDN alongside causes two Tailwinds to fight.
- **Final fix for glassmorphism:** Removed CDN entirely. Used `HTML()` from crispy_forms to render raw `<button>` and `<a>` elements with Tailwind classes — unfold's built-in Tailwind picks them up natively. No CDN, no conflict.

### What Nik learned
- **5-layer Django file upload pattern:** URL route → View (GET/POST) → Form (validates input) → Template (`enctype="multipart/form-data"`) → Model save (`objects.create` with `FileField`). Every Django upload has these 5 layers.
- **`request.FILES` dict:** Django parses multipart POST into `request.POST` (text fields) + `request.FILES` (binary). The key in `request.FILES` matches the form field name. View passes both to form: `UploadDocumentForm(request.POST, request.FILES)`.
- **`enctype="multipart/form-data"`:** Without it, the browser sends form data as URL-encoded text — file bytes get lost. `multipart` splits text from binary into separate MIME parts.
- **GET vs POST in views:** GET = "show me the form" (creates empty form, renders template). POST = "process my submission" (validates form, saves data, redirects).
- **`upload_to='path/%Y/%m/'`:** Django's `strftime` placeholders auto-organize files by year/month. `%Y` = 4-digit year, `%m` = 2-digit month. File lands at `MEDIA_ROOT/diagnosis_documents/2026/10/filename.pdf`.
- **Admin context variables:** `opts` (model metadata), `has_change_permission`, `is_popup`, `app_label` — normally set by `ModelAdmin` automatically. Custom views extending `View` must provide them manually via `context.update()` so admin chrome (breadcrumbs, sidebar) renders correctly.
- **`has_permission`:** Site-wide flag from `AdminSite.each_context()`. Controls whether user sees full admin navigation. Overriding it to `False` kills breadcrumbs/sidebar. Let `each_context` set it; don't override.
- **`context.update()` order matters:** Later updates overwrite earlier ones. If `each_context` sets `has_permission=True`, don't override with `False` afterward.
- **`change_list_template`:** Class attribute on `ModelAdmin` that tells Django which template to use for the changelist page. Without it, Django uses the default `admin/change_list.html` — custom buttons don't appear.
- **`{{ block.super }}` in template blocks:** Renders the parent's content of that block. Without it, you REPLACE the block instead of adding to it (e.g. removing the default "Add" button).
- **`form.helper.form_tag = False`:** Tells crispy_forms NOT to render its own `<form>` tag. The template already has `<form>` — if crispy renders another, you get nested forms (broken).
- **Tailwind CDN vs unfold's built-in Tailwind:** Unfold ships compiled Tailwind CSS. Loading `cdn.tailwindcss.com` alongside causes two Tailwind engines to conflict — classes get overridden, text disappears, hover breaks. Solution: don't use the CDN; unfold's Tailwind handles classes natively.
- **`FileExtensionValidator` syntax:** `FileExtensionValidator(['pdf', 'png'])` — NOT `FileExtensionValidator==(['pdf', 'png'])`. The `==` is a comparison operator, not a function call. Python evaluates it to `False`, Django sees `validators=[False]`, errors.
- **`css_class` in crispy_forms `Submit`:** Passes the string as the HTML `class` attribute on the rendered `<input type="submit">`. But `<input>` doesn't render text content well — better to use `HTML()` to render a raw `<button>` for full control.
- **`AdminSite.each_context()` source:** `venv/.../django/contrib/admin/sites.py` — the authoritative source for site-wide admin context variables.
- **Admin/ML engineer role boundary:** Admin owns the domain layer (keyword curation, topic approval, manual corrections). ML engineer owns the model layer (architecture, training pipeline, evaluation). The handoff: modeler trains → admin reviews discovered → ML engineer adjusts modeler → retrain. Same loop a content moderation team has with the team that trains the toxicity classifier.
- **"Not getting Deloitte" is diagnostic, not verdict:** Rejection gives feedback. Reapply Q1 2027 with DRF + FastAPI added. One application outcome doesn't define a 30-year career.
- **Nik's career positioning:** AI Engineer (not ML Engineer). Builds systems that USE models — pipelines, APIs, infrastructure. PersonalRAG (cross-encoder reranking) + Sentiri (BERTopic + XLM-R + Django) = textbook AI Engineer portfolio. Title: "AI Engineer" on resume, LinkedIn, Deloitte application.

### What we went through together
- Nik flagged the existing `DiagnosisDocument.file_path` was a CharField ("Cloud/S3 path or server path") — not a real FileField. Caught a real model design flaw.
- Hit `FileExtensionValidator==([...])` typo — `==` instead of `(`. Python didn't error at parse time; only Django's system check caught it (`validators[0] (False) isn't a function`). Lesson: read error messages carefully.
- Hit `IntegrityError: UNIQUE constraint failed` again (same pattern as earlier session — leftover rows from prior test). Test-fixture hygiene still a known smell.
- Nik noticed breadcrumbs missing after building the view. Diagnosed: `has_change_permisssion` (3 s's) + `has_permission: False`. Two bugs in `render_template` context. Fixed both.
- Nik wanted glassmorphism buttons. First attempt with Tailwind CDN conflicted with unfold's built-in Tailwind. Pivoted to `HTML()` from crispy_forms for raw `<button>` rendering — full control, no CDN, no conflict.
- Nik dodged the `form_tag = False` prediction question — still unpaid. Added to viva sweep.

### Glassmorphism CSS reference (for viva / future use)
| CSS property | Effect | Tailwind class |
|---|---|---|
| `border-radius: 9999px` | Full pill shape | `rounded-full` |
| `background: rgba(255,255,255,0.7)` | Semi-transparent white (glass) | `bg-white/70` |
| `backdrop-filter: blur(12px)` | Blurs content behind element (frosted) | `backdrop-blur-md` |
| `border: 1px solid rgba(255,255,255,0.2)` | Subtle glass edge | `border border-white/20` |
| `box-shadow: 0 4px 6px...` | Soft floating shadow | `shadow-lg` |
| `transition: all 0.2s` | Smooth animation | `transition-all duration-200` |
| `transform: translateY(-1px)` on hover | Tactile lift | (custom hover) |

---

## 2026-10-07 — Admin forms marathon: 5 custom views built solo (AutismDiagnosis → ClientSpecifier)

### What we did today
- Built 5 custom admin forms following the 5-layer pattern (Form → View → Template → URL → Button):
  1. **AutismDiagnosisForm** — client FK (autocomplete), diagnosed_by FK (doctor), support_level (ChoiceField), diagnosis_date (DateInput), clinical_notes (Textarea), is_active (Checkbox). No file — no `enctype`. First form without a FileField.
  2. **MasterSpecifierForm** — specifier_name, specifier_category, is_positive_specifier, dsm_code, is_active. All text/checkbox fields.
  3. **MasterSpecialtyForm** — specialty_name, specialty_code, category (ModelChoiceField to MasterSpecialtyCategory), is_active.
  4. **MasterSpecialtyCategoryForm** — category_name, category_code, category_description, is_active.
  5. **ClientSpecifierForm** — the complex one: autism_diagnosis FK (filtered is_active=True), specifier FK, severity (ChoiceField), is_present (BooleanField), clinical_notes (Textarea), stated_by FK (doctor), stated_date (DateInput), is_approved (BooleanField). Bridge table — no `client` field because client is derived through `autism_diagnosis.client`.
- Each form built with the same architecture: `forms.Form` + `FormHelper` + `Layout` + `Fieldset` + `HTML()` for raw glassmorphism buttons. All views extend `UnfoldModelAdminViewMixin` + `View`. All templates extend `admin/base_site.html`. All URLs wired via `get_urls()` in the respective `ModelAdmin`. All buttons via `change_list_template` override.
- Taught: `ModelChoiceField` (FK, needs `queryset=`) vs `ChoiceField` (static `choices=`). `UnfoldAdminTextInputWidget` (single-line `<input>`) vs `forms.Textarea` (multi-line `<textarea>`). `DateInput(attrs={'type': 'date'})` for native browser date picker. `BooleanField(required=False)` for checkboxes (otherwise form can't submit unchecked).
- Taught: `render_to_string(template_name, context, request)` — 3rd param is `request` for context processors (historical backward compat). `render(request, template_name, context)` is the modern shortcut — different arg order, returns HttpResponse.
- Taught: `form_tag = False` — crispy_forms doesn't render its own `<form>` tag. Template already has one. Without `False`, you get nested forms (invalid HTML).
- Taught: `permission_required` — maps to Django's 4 auto-generated model permissions (view/add/change/delete). Superusers bypass. For create forms, use `add_<model>`.
- Taught: `__init__(*args, **kwargs)` — `*args` carries `request.POST`/`request.FILES`, `**kwargs` carries extra options. `super().__init__(*args, **kwargs)` forwards to Django's `BaseForm` so `is_valid()` and `cleaned_data` work.
- Taught: ClientSpecifier bridge table design — no `client` field because client is reachable through `autism_diagnosis.client`. Adding a separate `client` FK would be denormalization (redundant, inconsistent risk). Third normal form.
- Taught: `MasterSpecialtyCategory` FK on `MasterSpecialty` uses `ModelChoiceField` with `queryset=MasterSpecialtyCategory.objects.filter(is_active=True)`. Dropdown renders each category as `<option>`.

### What Nik learned
- **The 5-layer pattern is now muscle memory.** Built ClientSpecifier (rep 7) completely solo — form, view, template, URL, button — without me spec'ing a single line.
- **Bridge tables don't need redundant FKs.** ClientSpecifier links AutismDiagnosis → MasterSpecifier. The client is derived through `autism_diagnosis.client`, not stored separately. Normalization principle.
- **`ModelChoiceField` vs `ChoiceField`:** FK → ModelChoiceField + `queryset=`. Static choices → ChoiceField + `choices=`. Mixing them up = `TypeError: missing 1 required positional argument: 'queryset'`.
- **Trailing comma turns string into tuple:** `change_list_template = 'path',` → tuple, not string. Django silently breaks. Check trailing commas.
- **Missing `return` in `get_urls()`:** Python returns `None` by default. Django URL resolver gets `None` → `ImproperlyConfigured: URLconf 'None'`. Every `get_urls()` must end with `return custom + urls`.
- **Admin class name shadowing:** `class MasterSpecialtyCategory(admin.ModelAdmin)` shadows the model class. After line runs, `MasterSpecialtyCategory` points to admin class (no `_meta`). Always use `Admin` suffix: `MasterSpecialtyCategoryAdmin`.
- **`form_tag = False`:** crispy_forms doesn't render `<form>` tag. Template already has one. Without `False`, nested forms (invalid HTML).
- **`*args, **kwargs` in `__init__`:** Forwards `request.POST`/`request.FILES` to Django's `BaseForm`. Without `super().__init__(*args, **kwargs)`, form is unbound — `is_valid()` always fails, `cleaned_data` is empty.
- **`permission_required`:** Maps to Django's model-level permissions (view/add/change/delete). Superusers bypass. For create forms: `add_<model>`.
- **`render_to_string` arg order:** `(template_name, context, request)` — `request` is 3rd for historical backward compat. Needed for context processors to fire (`{{ user }}`, `{{ messages }}`).
- **DaisyUI + unfold:** DaisyUI is a Tailwind plugin (not a separate engine). Loading DaisyUI CDN adds component classes without conflicting with unfold's built-in Tailwind. Fine for FYP demo; compile into Tailwind build for production.
- **DOM mastery > React:** Nik realized understanding DOM/CSS is the foundation; React is a DOM generator on top. Learning DOM first makes React easy later. Senior insight.
- **Nik's career positioning locked:** AI Engineer (not ML Engineer). Builds systems that USE models — pipelines, APIs, infrastructure. PersonalRAG + Sentiri = textbook AI Engineer portfolio.

### What we went through together
- Nik hit 8 bugs across 5 forms. Each bug was a single-character or single-line mistake (typo, missing return, trailing comma, class name shadowing). Diagnosed each from the traceback, fixed, moved on.
- Nik's growing confidence visible: rep 7 (ClientSpecifier) built completely solo. "wuhuuu ahahahha done everything working really well" = competence registering in body.
- Reinforced: function first, polish later. Glassmorphism buttons come after the form works end-to-end.
- Nik asked "am I great?" — honest answer: not great yet, but on the path. Consistency > talent. 4 years of showing up > raw IQ.

## 2026-10-08 — Admin dashboard + client cards + charts (KPI, doughnut, radar, cohort, progress line)

### What we did today
- Built the unfold admin dashboard (`templates/admin/index.html` + `chat_analyzer/dashboard.py`):
  - **KPI cards:** total clients, conversations, active topics, documents (4 stat boxes)
  - **Doughnut chart:** overall sentiment breakdown (positive/negative/neutral) using Chart.js
  - **Radar chart:** topic distribution (messages per active topic)
  - **Cohort table:** topic × sentiment matrix with color-coded cells (green/red/gray/blue, rounded-xl)
- Wired `DASHBOARD_CALLBACK` in settings.py pointing to `chat_analyzer.dashboard.dashboard_callback`
- Added "Analytics Dashboard" to unfold SIDEBAR navigation with `reverse_lazy` (not `reverse` — settings loads before URLs)
- Built **Client Card View** (`ClientCardView` in admin.py):
  - Card grid: 9 clients, 3 per row, responsive
  - Per-card data: name, phone, avatar initials, autism diagnosis (level + display), document count, specifier count
  - Topic breakdown badges (from `ClientTopicScore`): color-coded by score (green > 1, red < 0, gray = 0)
  - **Single-line progress chart:** daily summed sentiment_score over time (XLM-R confidence-weighted), one green line with filled area
  - Sentiment totals footer: positive / negative / neutral counts
- Added "Client Cards" to unfold SIDEBAR navigation
- Fixed `json.dumps()` bug: Python dict → single quotes → `JSON.parse()` fails. Must `json.dumps()` before passing to template for Chart.js.
- Fixed `return` indentation bug: `return self.render_template(...)` was inside `for client` loop → only rendered 1 card. Dedented outside loop → all 9 cards render.
- Fixed `.count()` bug on `total_clients`: `User.objects.filter(...)` returns queryset, not number. Must `.count()`.

### What Nik learned
- **`reverse_lazy` vs `reverse`:** settings.py loads before URL patterns are defined. `reverse()` tries to resolve immediately → `NoReverseMatch`. `reverse_lazy()` returns a deferred object that resolves later when the sidebar renders.
- **`json.dumps()` for Chart.js:** Django template renders Python dicts with single quotes (Python `str()`). Chart.js calls `JSON.parse()` which requires double-quoted JSON. Must `json.dumps()` in the view before passing to template. This is the #1 cause of "chart doesn't render" bugs.
- **Cohort component data structure:** `{"headers": [{"title": ..., "subtitle": ...}], "rows": [{"header": {...}, "cols": [{"value": ..., "color": "...tailwind classes..."}]}]}`. The `color` key on each cell applies Tailwind classes directly — unfold's cohort template reads `col.color` and injects it.
- **Unfold's built-in Chart.js:** Unfold ships Chart.js in its JS bundle. Supports `data-type="bar"`, `"line"`, `"doughnut"`, `"radar"`, `"pie"`. The JS reads `data-value` attribute on `<canvas class="chart">` and calls `new Chart(ctx, {type: ..., data: JSON.parse(data-value)})`.
- **Progress chart design — single line vs 5 lines:** Started with 5 topic lines (complex, messy). Simplified to 1 line (overall sentiment progress). Y-axis = `Sum(sentiment_score)` per date. Rising = improving, falling = declining. The `sentiment_score` is XLM-R's confidence-weighted score from -1.0 to +1.0.
- **`next(iterator, default)`:** Python built-in. Returns first matching item from an iterator, or `default` if no match. Used for looking up a topic's score for a specific date in the progress data. (Replaced by simpler single-line query.)
- **Return indentation in loops:** A `return` inside a `for` loop exits after the first iteration. Must dedent `return` OUTSIDE the loop so all iterations complete. Same bug pattern as missing `return custom + urls` in `get_urls()`.
- **Admin template resolution order:** project `templates/` > app `templates/` > Django built-ins. `templates/admin/index.html` (project root) overrides unfold's default. `chat_analyzer/templates/chat_analyzer/admin/...` is app-specific.
- **`DASHBOARD_CALLBACK`:** Unfold setting that points to a function receiving `(request, context)`. Function adds data to context dict → template renders it. Called before `admin/index.html` renders.
- **`{{ variable|safe }}` template filter:** Tells Django not to HTML-escape the output. Required for JSON data passed to `data-value` attributes — without `|safe`, Django escapes quotes as `&quot;` and `JSON.parse()` fails.
- **Unfold SIDEBAR navigation config:** `UNFOLD["SIDEBAR"]["navigation"]` is a list of sections. Each section has `title`, `separator`, `collapsible`, `items`. Each item has `title`, `icon` (material-symbols-outlined name), `link` (use `reverse_lazy`).
- **DaisyUI + unfold:** DaisyUI is a Tailwind plugin (not a separate engine). Can load DaisyUI CDN alongside unfold without conflict. Adds component classes (`btn`, `card`, `badge`, `table-zebra`).

### Bugs hit today
| Bug | Root cause | Fix |
|---|---|---|
| Charts not rendering | Python dict → single quotes → `JSON.parse()` fails | `json.dumps()` in view |
| Only 1 card rendered | `return` inside `for client` loop | Dedent `return` outside loop |
| `total_clients` not showing | `User.objects.filter(...)` returns queryset, not number | Add `.count()` |
| `chart_data` built per topic | `chart_data` + `cards.append` inside topic loop | Dedent outside topic loop |
| `date` vs `d` variable mismatch | `for d in dates:` but checking `p['date'] == date` | Change `date` to `d` |
| `card.client_get_full_name` | Missing dot between `client` and `get_full_name` | `card.client.get_full_name` |
| Duplicate "No active diagnosis" text | Copy-paste error in template | Remove duplicate line |

### MVP gap analysis
- Created `MVP_GAP_ANALYSIS.md` at project root. Audited proposal vs codebase:
  - **15 features completed** (user mgmt, WhatsApp import, sentiment, topic modeling, admin dashboard, clinical models, etc.)
  - **8 features missing** (client-facing dashboard, therapist dashboard, DRF, test suite, evaluation metrics, RBAC view enforcement, per-client detail, TopicTrend population)
  - **5 features partial** (topic quality, signal guard verification, ClientTopicScore recompute, RBAC, batch UI)
  - MVP completion: ~65%. Recommended 5-6 week build plan to demo day.

### What's next (from MVP_GAP_ANALYSIS.md)
1. **Run 8: Kill garbage topics** — `buka-nangis-baru`, `child-has-the`, `menangis tidur-mampu-suka bagus`. Fix cleaner (English stopwords), fix c-TF-IDF. URGENT for demo.
2. **Viva sweep:** Run 7-print signal guard test. Answer unpaid viva questions.
3. **Client-facing dashboard** — separate from admin. Clients log in, see own data only.
4. **Therapist dashboard** — filtered to assigned clients only.
5. **RBAC view-level enforcement** — therapist sees assigned clients, doctor sees diagnosed clients, client sees own data.
6. **Per-client detail page** — drill-down with trend chart + topic breakdown.
7. **Tests + evaluation metrics** — smoke tests + sentiment accuracy + topic coherence.
8. **DRF endpoints** — serializers + views + role-based permissions. Deloitte reapply strength.

---

## 2026-10-08 (evening) — DSM-5 specifiers seeded + definition field + specifier display on client cards

### What we did
- Extracted official DSM-5 Autism Spectrum Disorder specifiers from the DSM-5 PDF (page 88, 299.00 / F84.0). 10 specifiers total:
  - With/without accompanying intellectual impairment (Intellectual)
  - With/without accompanying language impairment (Language)
  - Associated with known medical/genetic condition (Medical)
  - Associated with known environmental factor (Environmental)
  - Associated with another neurodevelopmental disorder (Neurodevelopmental)
  - Associated with another mental disorder (Mental)
  - Associated with another behavioral disorder (Behavioral)
  - With catatonia (Behavioral)
- Created `seed_specifiers.py` management command with all 10 DSM-5 specifiers + DSM codes.
- Added `definition = models.TextField(blank=True, null=True)` to `MasterSpecifier` model. Migration applied.
- Updated seed command: switched `get_or_create` → `update_or_create` so existing specifier rows get the `definition` field updated (get_or_create wouldn't update existing rows).
- Updated `ClientCardView` to pass `cs.specifier.definition` in `specifier_data` dict.
- Updated `client_card.html` template: definition shown as small gray text below each specifier name (Option D — always visible, no JS needed).
- Taught all 10 DSM-5 specifiers in detail: what each means, clinical examples, why each matters for treatment planning.

### What Nik learned
- **DSM-5 specifiers individualize the autism diagnosis:** "with/without" specifiers define cognitive/language profile. "Associated with" specifiers identify co-occurring conditions. "With catatonia" flags a medical emergency.
- **`get_or_create` vs `update_or_create`:** get_or_create only creates if not exists — won't update. update_or_create updates existing rows with new field values. Needed update_or_create to add definitions to already-seeded specifiers.
- **`definition` field = clinical decision support:** therapists see the specifier name AND its plain-English explanation on the client card. The system teaches the clinician — that's the product value proposition.
- **DSM-5 specifiers affect treatment:** knowing a client has "with intellectual impairment" + "associated with ADHD" changes the therapy plan. The specifiers aren't labels — they're action items.

### What's next (unchanged from MVP_GAP_ANALYSIS.md)
1. Run 8: Kill garbage topics — URGENT for demo
2. Viva sweep: signal guard test + unpaid questions
3. Client-facing dashboard
4. Therapist dashboard
5. RBAC view-level enforcement
6. Per-client detail page
7. Tests + evaluation metrics
8. DRF endpoints

---

## Session: E-Commerce Stripe Project (2026-10-14)

### What we built
Built a complete Django e-commerce app with Stripe payment gateway from scratch. Separate learning project at `~/degree/ecommerce_project` (git: `nickaqmal02/django_ecommerce_stripe`).

### Features implemented
- Product catalog with categories (Apparel, Accessories, Home Goods)
- Multiple images per product (ProductImage inline admin)
- Session-based shopping cart (add/remove/update quantity)
- Checkout form (email, name, phone, shipping address)
- Stripe Checkout integration (card + FPX)
- Webhook handling (PENDING → PAID) with CSRF exemption + signature verification
- Email receipt via Mailtrap sandbox (HTML email template)
- PDF receipt generation via WeasyPrint
- Order tracking page (enter order ID → see courier + tracking number)
- Admin: courier dropdown + tracking number (inline editable)
- django-unfold dark admin theme
- Category gallery on homepage (hover overlay, 3-column landscape)
- Secrets moved to .env (python-dotenv)
- Production prep: render.yaml, build.sh, Procfile, gunicorn, dj_database_url
- Dynamic URLs (get_base_url) for production deployment

### Key lessons learned
- **Stripe `payment_method_types` deprecated** — payment methods now managed in Dashboard
- **Stripe SDK uses `.id` not `.get('id')`** — Session objects aren't dicts
- **Webhook needs `@csrf_exempt`** — Stripe POST has no CSRF token
- **Two terminals required** — Django server + `stripe listen` for webhooks
- **SSH key in project dir = bad** — must live in `~/.ssh/`, never in git
- **Git filter-branch** removes secrets from history: filter → clean refs → gc → force push
- **Money stored as IntegerField (sen)** — floating point errors make floats unsafe for currency
- **Render free tier = no credit card** — but Malaysian debit cards get blocked for international charges

### What's next
1. Call bank to enable international card transactions
2. Deploy on Render (render.yaml ready, env vars prepped)
3. Set up production Stripe webhook (add endpoint in Stripe dashboard)
4. Push latest code to GitHub (SSH key re-added to GitHub)

---

## 2026-10-15 — Frontend polish marathon: Apple design system across all role dashboards

### What we did
- **Client portal fixes:** Patched 2 template bugs — `client_therapist.html` (missing `=` before `{{ }}`, therapist name invisible) and `client_settings.html` (broken `<div class="flex" </div>` tag). Verified therapist name "Aina Razak" renders.
- **Admin analytics dashboard rebuilt** (`templates/admin/index.html` + `dashboard.py`): 6 KPI cards, sentiment doughnut + trend line, topic distribution with 2D bar / 3D toggle, DSM-5 doughnut, topic×sentiment heatmap, therapist workload.
- **3D graph saga (the hard-won lesson):** Wanted an Obsidian-style 3D network. Tried `graph3D` series → **doesn't exist in ECharts GL** (blank chart). Tried `lines3D` (plural) → **broken in echarts-gl@2.0.9**, crashes `Cannot read properties of undefined (reading '0')`. Tried `{coords:...}` vs `{value:...}` data formats. **The working combo: `scatter3D` (nodes) + `line3D` (singular, connections).** Also hit the classic ECharts hidden-container bug — chart renders tiny (quarter-size) when init'd inside `display:none`, fixed with `chart3d.resize()` on toggle reveal.
- **Client cards** (`client_card.html`): fixed duplicate-date chart bug (was grouping by topic, creating duplicate x-labels), added combo chart (line+bar dual axis), message count pill, sentiment percentages.
- **Login page** polished: glassmorphism card, gradient blob background, "Back to Main Page" link to welcome view.
- **Welcome page** — role-themed backgrounds on hover (admin=indigo, therapist=green, doctor=blue, client=orange), then rebuilt in **Apple design language** (SF Pro, #f5f5f7, 18px radius, cubic-bezier easing).
- **Created `docs/apple-design-system.md`** — the canonical reusable design system (font stack, palette, typography scale, card/chip components, the Apple easing curve, entrance animations, role-swap JS, application checklist).
- **Applied Apple system to admin dashboard + client cards** — removed ALL gradients, flat #fff cards, #0071e3 accents, #f5f5f7 neutrals.
- **Therapist side rebuilt** (`MainTherapist/dashboard.html` + `ClientTherapist/client_detail.html`): old Bootstrap template used non-existent fields (`parent_name`, `child_name`, `status`). Rebuilt with actual model fields + Apple design. Added KPIs, client cards grid, drill-down detail page.
- **Therapist chat upload** (`therapist_upload_chat`): therapists can now upload WhatsApp .txt for their OWN assigned clients. Created `TherapistUploadChatForm` (client field scoped to `assigned_therapist`), chat_type dropdown (individual/group/admin), auto-assigns therapist=self. Reuses `process_whatsapp_upload` + `train_topics()`. Verified end-to-end: 25 messages saved with `chat_type=group`, `uploaded_by=therapist1`.
- **Created `docs/therapist-role.md`** — full therapist capability doc.
- **Therapist sample login:** all therapists password reset to `therapist123` (therapist1=Aina Razak 3 clients, therapist2=Daniel Tan 3, therapist3=Farah Ismail 2, therapist4=Kumar Raj 2, therapist05=ain shahirah 0).

### What Nik learned
- **ECharts GL series types are a trap:** `graph3D` doesn't exist. `lines3D` (plural) is broken. Only `scatter3D`, `line3D` (singular), `bar3D`, `surface` are reliable. Read the actual option-gl docs, don't guess series names.
- **Hidden-container chart bug:** any Chart.js/ECharts chart initialized inside `display:none` measures 0×0 → renders tiny. Always `resize()` after the container becomes visible.
- **Template variable typos are invisible bugs:** missing `=` before `{{ }}` renders the name as an HTML attribute (invisible), not text. Django doesn't error — it just silently renders wrong.
- **`json.dumps()` before template + `|safe` filter + `decode()` in JS** = the three-part contract for passing Python data to Chart.js.
- **Form field scoping = security:** `ModelChoiceField(queryset=...)` limited to `assigned_therapist=request.user` prevents a therapist uploading for another therapist's client.

### What's next (unchanged priorities)
1. Run 8 garbage-topic cleanup (URGENT for demo)
2. Doctor dashboard (still renders broken `doctor_dashboard.html` — same treatment as therapist)
3. Viva sweep: signal guard test + unpaid questions
4. Tests + evaluation metrics
5. DRF endpoints

---

## 2026-10-15 (evening) — Therapist role + chat upload complete

### What we did
- Built therapist dashboard + client detail + upload chat (documented above).
- Therapist upload verified: `chat_client10.txt` uploaded for FauziArif as `group` chat by therapist1 — 25 messages saved, sentiment applied, topic retraining kicked off (MPS/XLM-R).
- Left the test data in place (Nik's call: "leave it mate") — FauziArif now has +25 messages from the test upload.

---

## 2026-10-15 (late) — Topic QUALITY closed: garbage discovered topics eliminated (Run 9)

### Root cause (three stacked leaks, found by live probe — NOT the old memory)
1. **Domain-words drift (the big one):** `domain_words_topic.txt` (1166 words) had ballooned into a general English wordlist. `child`, `children`, `staff`, `better`, `good`, `great`, `friendly`, `here` etc. were all in the "KEEP" file. The cleaner checked `if word in domain_words_topic` BEFORE stopwords, so any junk in that file bypassed ALL cleaning. That's how `child-has-the` formed.
2. **Naming bypass:** the discovered-topic fallback used raw c-TF-IDF keywords (`"-".join(keywords[:3])`) with zero filtering — no stopword check, no bigram check. Produced `menangis tidur-mampu-suka bagus`.
3. **Near-empty texts:** texts cleaning down to 1-2 words (`sesuatu`, `mampu`, `terima kasih`) were still trained, creating coincidence clusters.

### The fixes (3, all in `text_cleaner.py` + `topic_modeler.py`)
1. **Cleaner precedence flip:** stopwords now WIN over domain words. Order: stem → if in stopwords → skip → if in domain words → keep → if len > 2 → keep.
2. **Naming unified:** new `_topic_name_from_keywords()` helper — stopwords first, bigrams skipped, " - " join. Both `get_topic_name()` and the discovered-topic fallback route through it.
3. **Empty-text filter:** `preprocess_messages` drops < 2 content words.
Plus: added ~130 English stopwords to `topic_stopwords.txt` (was Malay-only, 1235 → 1341).

### The stale-row catch (critical)
`--clean-first` does NOT clear old topics — only `--clear` does, and `--clear` wipes the 5 active seeded topics too (too destructive). So the old garbage `discovered` rows survived the retrain. Fixed surgically: deleted only `status='discovered'` topics + their MessageTopic links, left the 5 active topics intact.

### Final verified state
- **5 active topics, 0 discovered (garbage gone):** Behaviour (45), Progress (102), School (32), Sleep (54), Speech (100).
- Coverage audit of 243 conversations: 127 client-with-topic, 110 staff (correctly excluded), 4 empty/short (fix 3), **2 genuine gaps** (`fokus tunjuk buku tengok`, `sahabat tempat kerja sekolah`) = 0.8% miss rate.
- Mapper verified working: `malam tidur`→Sleep, `marah`→Behaviour, `perkembangan baik`→Progress, all fire correctly.

### What Nik learned
- **Data hygiene beats algorithm tuning.** The garbage wasn't HDBSCAN or c-TF-IDF — it was a word-list that drifted into general English. A 5-line precedence flip (stopwords beat domain words) fixed what weeks of "tune the clustering" would not.
- **`--clean-first` vs `--clear` are different things.** clean-first re-cleans text; clear wipes topic rows. Running clean-first and expecting a fresh topic table = the exact confusion that left stale garbage rows.
- **Stale rows ≠ model output.** The training printed clean names, but the DB report read old names — because the old rows were never deleted. Always distinguish "what the model produced" from "what the DB still holds."
- **Coverage isn't "every message gets a topic."** Staff messages are correctly excluded (topics model client behavior, not therapist/admin chat). Counting them as "missed" would be wrong.

### What's next (the real remaining work, now that topics are clean)
1. Viva sweep: signal guard test + unpaid questions.
2. Doctor dashboard already built (see above) — verify it renders with the clean 5-topic data.
3. Tests + evaluation metrics (sentiment accuracy, topic coherence scores).
4. DRF endpoints.

---

## 2026-10-16 — Infrastructure migration: SQLite → PostgreSQL + Celery/Redis async stack

### What we did
- **Why:** App needs to deploy to Render. Render's ephemeral filesystem wipes SQLite on every
  deploy — PostgreSQL is a deployment requirement, not a preference. Nik confirmed from prior
  e-commerce project experience.
- **PostgreSQL 17.11 installed via Homebrew**, started as a background service (`brew services start`).
  Created user `nik` + database `sentiri_chat`. Verified connection.
- **Redis 8.10 installed via Homebrew**, started as background service. Verified PONG.
- **Python packages installed in venv** (Python 3.14.7): `psycopg[binary]` (Postgres driver),
  `dj-database-url` (env-based DB switching — the Render pattern), `python-dotenv`, `celery==5.6.3`,
  `redis==8.1.0`. Django remains at 6.1.1 (Celery 5.6 is compatible).
- **Settings refactor (`settings.py`):**
  - `load_dotenv()` at top — loads `.env` for local dev (Render injects env vars directly).
  - `DATABASES` now env-aware: if `DATABASE_URL` set → PostgreSQL via `dj_database_url.config()`
    with `conn_max_age=600` (pooling) + `conn_health_checks=True`; if `USE_SQLITE=1` or no
    `DATABASE_URL` → SQLite fallback. This is the standard Render deployment pattern.
  - Celery config block: `CELERY_BROKER_URL` + `CELERY_RESULT_BACKEND` from `REDIS_URL` env var.
- **`celery.py` created** in project package — standard Django+Celery integration:
  `app = Celery('finalyearengineredo')`, `config_from_object('django.conf:settings')`,
  `autodiscover_tasks()`. `__init__.py` updated to export `celery_app`.
- **`.env` created** with `DATABASE_URL`, `REDIS_URL`, `USE_SQLITE=0`. Added `.env` to `.gitignore`.
- **Data migration:** `dumpdata` from SQLite (USE_SQLITE=1 flag) → 876 objects → `loaddata` into
  PostgreSQL. Verified row counts match: 20 users, 243 conversations, 5 topics, 333 messagetopic,
  4 chatthreads, 15 chatmessages, 56 uploadhistory. Zero data loss.
- **Celery worker tested:** started worker, `inspect ping` → `celery@apples-MacBook-Pro.local: OK`.
  Full stack alive: Postgres + Redis + Celery + Django.
- **`requirements.txt` updated** with new packages + comments.

### What Nik learned
- **`dj_database_url` is the Render pattern.** You don't hardcode `DATABASES` — you let
  `DATABASE_URL` env var switch between dev (SQLite) and prod (Postgres). One settings file,
  two environments.
- **`conn_max_age=600`** = connection pooling. Without it, Django opens a new DB connection per
  request (expensive on Postgres). With it, connections are reused for 10 minutes.
- **Celery architecture:** Django (producer) → Redis (broker/message bus) → Celery worker (consumer).
  Django hands a task to Redis; Redis holds it; the worker picks it up. Three processes, one pipeline.
- **`app.autodiscover_tasks()`** scans every installed app for `tasks.py` — that's where we'll
  put the delayed ML analysis function.
- **Python version matters.** System Python is 3.9.6 (can't run Django 6.x). Venv Python is 3.14.7.
  Always activate venv before pip install — or you install into the wrong Python.

### What's next (the actual feature, now that infra is ready)
1. Write `chat_analyzer/tasks.py` — `@shared_task` that takes a Conversation ID, runs
   `clean_text → XLM-R predict → TopicMapper.match`, writes results back. Delay = `countdown=300`.
2. Write the bridge: when a client sends a `ChatMessage`, create a `Conversation` row (is_from_client=True,
   chat_type='individual') and fire the Celery task with 5-min delay.
3. Verify end-to-end: send chat message → wait 5 min → see sentiment + topic on the Conversation row.
4. Only client messages get bridged (therapist replies → is_from_client=False, excluded from topics,
   same as WhatsApp staff exclusion).

---

## 2026-10-16 (cont.) — Async ML pipeline BUILT + VERIFIED: tasks.py + bridge + Celery

### What we did
- **`chat_analyzer/tasks.py` created** — `@shared_task analyze_live_message(conversation_id)`:
  1. Load Conversation row (return early if not found / already analyzed — idempotent)
  2. `clean_for_sentiment()` → write `cleaned_text` + `is_cleaned_sentiment=True`
  3. `analyze_sentiment()` (XLM-R) → write `sentiment`, `sentiment_score`, `sentiment_confidence`
  4. `clean_for_topic_modeling()` → write `cleaned_text_topic` + `is_cleaned_topic=True`
  5. Save (sentiment + cleaned text persisted even if topic mapping fails)
  6. If `is_from_client=True`: `TopicMapper.map_message_with_alternatives()` against 5 active topics
  7. Write `MessageTopic` rows (same `update_or_create` pattern as `topic_modeler.py`)
  8. Set `is_processed=True`, save, return result dict
  - Staff messages (`is_from_client=False`): sentiment only, topic mapping skipped (same exclusion as WhatsApp)
  - `max_retries=3`, `default_retry_delay=60` — if XLM-R fails, Celery retries in 1 min

- **Bridge wired in `views.py:chat_thread_detail`** — after `ChatMessage.objects.create()`:
  1. Create a `Conversation` row (client, sender, is_from_client, date/time, message, chat_type='individual')
  2. `message_hash` = SHA256 of `live-{thread_id}-{user_id}-{timestamp}` (unique per message)
  3. `analyze_live_message.apply_async(args=[conv.id], countdown=300)` — 5-minute delay
  - Only fires for messages sent via the chat UI (not WhatsApp uploads — those have their own pipeline)

- **Celery 5.6 + Python 3.14 bug found and fixed:** `fast_trace_task` ValueError in prefork pool.
  Root cause: Celery 5.6's C-optimized trace path incompatible with Python 3.14's multiprocessing.
  Fix: `--pool=solo` (single-process worker). Settings: `CELERY_WORKER_POOL` env-configurable
  (solo for local dev, prefork for production where Celery 5.5+ or Python 3.12 may be used).

- **VERIFIED END-TO-END (2 tests):**
  - **Sync test** (direct function call): "anak saya tidur pukul 3 pagi semalam, risau betul"
    → Sentiment: negative (-0.95, conf 97%) → Topic: Sleep and Routine (primary, score=2.00) ✅
  - **Async test** (Celery worker, 15s delay): "anak marah and menangis kat sekolah hari ni"
    → Celery worker received task after 15s countdown → ran full pipeline in 1.56s
    → Sentiment: negative (-0.98, conf 99%) → Topic: Behaviour and Transitions (primary, score=3.50) ✅
  - Worker logs show: Sastrawi loaded (root words, typos, emoji, slang, domain words, stopwords)
    → XLM-R inference → TopicMapper → MessageTopic written to Postgres. Full pipeline reuse confirmed.

- **Test data cleaned up** — 3 test Conversation rows + 2 MessageTopic rows deleted. DB back to 243 conversations.

### What Nik learned
- **Pipeline reuse is the whole point.** The Celery task is 40 lines of glue code — it calls
  the SAME `clean_for_sentiment`, `analyze_sentiment`, `clean_for_topic_modeling`,
  `TopicMapper.map_message_with_alternatives` functions that `train_topics` uses. Zero ML code
  duplicated. One pipeline, two input sources (WhatsApp batch + live chat async).
- **`@shared_task(bind=True, max_retries=3)`** = self-healing tasks. If XLM-R hiccups, Celery
  retries automatically. `apply_async(countdown=300)` = the 5-minute delay lives in the Redis
  queue, not in Python's `time.sleep` — survives tab close, server restart, anything.
- **`--pool=solo` vs `--pool=prefork`:** prefork spawns child processes (parallelism, but
  triggers the Python 3.14 trace bug). Solo runs single-process (no parallelism, but reliable).
  For FYP scale (one therapist, few clients), solo is fine. Production would use prefork with
  a compatible Python version.
- **Idempotency:** the task checks `if conv.sentiment is not None: skip` — safe to retry without
  duplicating analysis. Same pattern as production task queues.
- **The bridge is the architectural decision:** ChatMessage stays UI-only (threading, read state).
  Conversation holds all ML fields. The bridge connects them at send time. One DB write for UI,
  one for ML, one Celery task for deferred analysis — three concerns, cleanly separated.

### What's next
1. Test through the actual chat UI (log in as client, send message, verify Conversation row appears).
2. Viva sweep: signal guard test + unpaid questions.
3. Doctor dashboard verification with clean 5-topic data.
4. Tests + evaluation metrics (sentiment accuracy, topic coherence).
5. DRF endpoints.

---

## 2026-10-16 (Phase 2 start) — RAG Pipeline: infra setup + models + service + Celery task + chatbot view + template (PARTIALLY COMPLETE)

### What we did
- **RAG dependencies installed** in venv: chromadb 1.5.9, langchain 1.4.6,
  langchain-community 0.4.2, langchain-text-splitters, pypdf, pymupdf, langchain-groq.
- **Models created + migrated** (`0013_chatquery_treatmentdocument.py`):
  - `TreatmentDocument` — tracks uploaded PDFs (status: pending→processing→ready/failed,
    chunks_created, uploaded_by scoped to doctor/admin, file upload to treatment_docs/)
  - `ChatQuery` — logs user questions + RAG answers + sources + confidence + response time
- **`rag_service.py` created** (full pipeline, ~400 lines):
  - `ingest_document(file_path, title)` — load PDF/txt → chunk (1000/200 overlap) →
    embed with `paraphrase-multilingual-MiniLM-L12-v2` → store in ChromaDB
  - `query(question)` — retrieve top 20 → rerank to top 5 (cross-encoder) →
    build context → generate answer via Groq LLM → return answer + sources + confidence
  - `get_collection_stats()` — chunk count for dashboard
  - `delete_document_chunks(title)` — cleanup
  - Singleton pattern: embedding model + reranker + ChromaDB loaded once, reused
  - **Key change from PersonalRAG:** embedding model switched from all-MiniLM-L6-v2
    (English) to paraphrase-multilingual-MiniLM-L12-v2 (Malay-compatible)
  - **Groq model change:** llama-3.3-70b-versatile deprecated → switched to
    openai/gpt-oss-120b (verified available via Groq API)
- **3 test Malay PDFs generated** (reportlab): terapi_pertuturan_autism.pdf,
  tingkah_laku_cabaran_autism.pdf, terapi_pemakanan_autism.pdf. Each 4-5K, multi-section,
  realistic Malaysian autism clinic content.
- **Ingestion verified:** 3 PDFs → 14 chunks in ChromaDB ✅
- **Full RAG pipeline verified end-to-end:** "Apakah teknik yang digunakan dalam terapi
  pertuturan untuk kanak-kanak autism?" → correct answer about PECS, AAC, floor time +
  5 sources cited + 99.85% confidence ✅
- **Celery task created** (`ingest_treatment_document` in tasks.py):
  - Takes document_id, loads TreatmentDocument, calls rag_service.ingest_document()
  - Updates status: pending→processing→ready/failed
  - max_retries=2, default_retry_delay=30
- **Views created:**
  - `chatbot_view` — renders chatbot page, shows recent queries + vector store stats
  - `chatbot_ask` — POST endpoint, calls rag_service.query(), logs to ChatQuery, returns JSON
  - `doctor_upload_document` — doctor/admin uploads PDF, creates TreatmentDocument,
    fires Celery ingestion task
- **URLs added:** /chatbot/, /chatbot/ask/, /dashboard/doctor/upload-document/
- **Chatbot template created** (`chatbot.html`):
  - Apple design, chat interface (user messages right blue, AI left grey)
  - Source chips under each answer
  - Typing indicator (animated dots)
  - Confidence + response time display
  - Fetch API for async question submission (no page reload)
  - Shows recent query history
  - Knowledge base status bar (chunk count)

### Also done this session (before RAG):
- **PostgreSQL migration:** SQLite → PostgreSQL 17 (db=sentiri_chat, user=nik).
  876 rows migrated, zero loss. `dj_database_url` env-aware settings (Render-ready).
- **Redis + Celery setup:** both installed, running, verified.
- **Async ML pipeline:** `tasks.py analyze_live_message` + bridge in views.py.
  Celery worker verified (sync + async, 15s delay test).
- **Timezone fix:** UTC → Asia/Kuala_Lumpur.
- **Therapist dashboard "Recent Analyzed Messages" widget:** table with sentiment +
  topic pills, sorted by message date (not import time).
- **Context processor:** `unread_counts` — red unread badge on every page.
- **Admin.py lazy import fix:** moved `upload_service` import from class body to
  method body. Django startup 5.5s → 0.3s (17× faster).
- **Chat template fixes:** scroll-to-bottom on send (both therapist + client),
  bubble sizing fix (removed extra wrapper div).

### What's NOT done yet (resume here)
1. ⬜ **Doctor upload document template** (`doctor/upload_document.html`) — form not created yet
2. ⬜ **Chatbot link on dashboards** — client/therapist/doctor navbars need link to /chatbot/
3. ⬜ **Celery worker test with actual document upload** — verified pipeline manually,
   but not through the web UI + Celery worker together
4. ⬜ **Client chatbot template** — `client/chatbot.html` (extends base_client.html)
5. ⬜ **End-to-end verify through browser** — log in as doctor, upload PDF, then log in
   as client, ask question, get answer

### What Nik learned
- **RAG = retrieval + generation.** The pipeline is: chunk → embed → store → retrieve →
  rerank → build context → LLM generate. Each step is a separate function, testable alone.
- **Multilingual embeddings matter.** all-MiniLM-L6-v2 is English-focused and would perform
  poorly on Malay. paraphrase-multilingual-MiniLM-L12-v2 handles both, same 384 dim.
- **Groq model names change.** llama-3.3-70b-versatile was deprecated. Always check
  `GET /v1/models` to see what's available before hardcoding.
- **Singleton pattern for ML models.** Embedding model + reranker load once, reuse across
  queries. Loading on every request would be 5s per question.
- **Same Celery pattern for RAG ingestion as live chat analysis.** Document upload fires
  `ingest_treatment_document.delay(doc_id)` — heavy PDF processing runs in background,
  user doesn't wait. Status tracked in TreatmentDocument model.


## 2026-10-17 — 1-on-1 Chat Feature (complete) + n8n Reservation Pipeline (started)

### What we did today

**Feature 1: Client ↔ Therapist 1-on-1 Live Chat — COMPLETE**
- Fixed 4 bugs in Nik's hand-typed views:
  1. `request.therapist` → `thread.therapist` (was reading attr off HttpRequest, not User)
  2. `therapist.request.user` → `therapist=request.user` (missing `=` = SyntaxError)
  3. `thread_id=thread_id` → `thread_id=thread.id` (undefined variable)
  4. Missing imports: `HttpResponseForbidden`, `timezone`, `ChatThread`, `ChatMessage`
  5. `@therapist_required` on `chat_thread_detail` → `@login_required` (manual role check inside) so both client + therapist can use same view
- Built 3 templates (Apple design): `MainTherapist/chat_threads.html` (inbox), `MainTherapist/chat_thread.html` (chat view), `client/chat_thread.html` (client side)
- Built WhatsApp-style read receipts: inline SVG double-ticks — grey (`rgba(255,255,255,0.6)`) for delivered, blue (`#34b7f1`) for read. Works on both therapist + client bubble colors.
- Fixed unread badge perspective bug: `chat_threads.html` was showing `thread.client_unread` (client's perspective) instead of `thread.therapist_unread` (therapist's perspective). Therapist's own messages don't show "N new" on their side — only messages FROM the client do.
- Added "Recent Chats" widget to therapist dashboard (top 5 threads by `last_message_at`, with avatar, last message preview, unread badge, timestamp)
- Added "Messages" segment to client sidebar nav (between "My Therapist" and "Settings"), with red unread badge
- Built `client_messages` view + `messages.html` template (client-side inbox, mirrors therapist's)
- Built `start_chat_with_therapist` view (client-side auto find-or-create thread)
- End-to-end verified: therapist sends → client views (unread resets) → client replies → therapist sees "1 new" → therapist views (unread resets). Security: non-member gets 403.

**Feature 2: n8n Reservation Chatbot — STARTED**
- Nik chose Option B: n8n as orchestration layer (not Django-native tool-calling)
- Booking rules confirmed:
  - Staff = therapist OR doctor (client can book with either)
  - 3-layer availability check: (1) office hours via `StaffSchedule`, (2) date exceptions via `StaffTimeOff`, (3) slot conflict via `SessionBooking`
  - Option C schedule model: recurring weekly pattern + specific date exceptions
- 3 new models written to `models.py`: `StaffSchedule`, `StaffTimeOff`, `SessionBooking`
  - Fixed `related_name` clash: both `client` and `staff` FKs pointed to `User` with `related_name='bookings'` → Django E304/E305. Changed to `client_bookings` / `staff_bookings`.
- 3 admin classes registered: `StaffScheduleAdmin` (list_editable for is_available/start_time/end_time), `StaffTimeOffAdmin` (date_hierarchy), `SessionBookingAdmin` (list_editable status, date_hierarchy)
- Migration created + applied by Nik
- n8n install in progress (npx n8n start — large dependency tree, ~400 integrations)
- API endpoints for n8n to call (`/api/check-availability/`, `/api/book-session/`) — NOT YET BUILT

### What Nik learned
- **PID = Process Identifier.** OS assigns a unique number to every running program. `kill -9 PID` sends SIGKILL (signal 9 = immediate, no cleanup). `kill PID` sends SIGTERM (signal 15 = polite, app can clean up). Production uses `systemctl restart` (SIGTERM → wait → SIGKILL). `lsof -ti :PORT` returns just PIDs for scripting: `kill -9 $(lsof -ti :8000)`.
- **n8n = visual orchestration.** Webhook trigger → process node (LLM/Code) → action node (HTTP/DB) → response. Same pattern as Django+Celery but visual. AI Agent node (v2.35+) does native tool-calling: LLM receives tools, decides which to call, gets result, generates reply.
- **Two FKs to same model need different related_names.** Django can't disambiguate `user.bookings` if both `client` and `staff` use the same reverse accessor. Fix: `related_name='client_bookings'` vs `'staff_bookings'`.
- **Read receipts = data already exists, just template work.** `ChatMessage.is_read` was already stored. WhatsApp ticks are just an inline SVG with conditional `stroke` color — no new model field, no new view logic.
- **Custom calendar > Google Calendar for FYP.** Three Django models (StaffSchedule + StaffTimeOff + SessionBooking) = complete 3-layer availability check. Google Calendar API is for phone sync at scale; custom shows you understand the problem.

### What's next (in order)
1. ⬜ n8n finishes installing → open `http://localhost:5678` → set up owner account
2. ⬜ Add Groq API credential in n8n
3. ⬜ Build Django API endpoints: `/api/check-availability/`, `/api/book-session/`, `/api/list-sessions/`
4. ⬜ Build n8n workflow: webhook → AI Agent node (Groq) → 3 HTTP tool calls → response
5. ⬜ Wire Django `chatbot_ask` view to call n8n webhook
6. ⬜ End-to-end test: client types "I want to book Tuesday 3pm" → n8n → booking confirmed
7. ⬜ Seed test data: StaffSchedule for all 5 therapists + 2 doctors (Mon-Fri 9-5)

## 2026-10-17 (continued) — n8n RESERVATION CHATBOT WORKING END-TO-END ✅

### What we did
- **n8n installed** via `npm install -g n8n --omit=optional` + rebuilt sqlite3 native binary manually.
  - n8n v2.43.7 running on `http://localhost:5678`
  - Start command: `n8n start`
- **DeepSeek API** chosen over Groq (cheaper, better tool calling). Model: `deepseek-flash` (renamed from `deepseek-chat` in late 2026).
- **n8n workflow built** in the visual editor:
  - Webhook node (POST `/sentiri-chat`, response mode: Respond to Webhook)
  - AI Agent node ("Agentic dude") with DeepSeek Chat Model sub-node
  - 4 HTTP Request tool nodes connected to AI Agent's Tools socket:
    1. `check_availability` → POST `http://0.0.0.0:8000/api/check-availability/`
    2. `book_session` → POST `http://0.0.0.0:8000/api/book-session/`
    3. `list_sessions` → GET `http://0.0.0.0:8000/api/list-sessions/`
    4. `staff_schedule` → GET `http://0.0.0.0:8000/api/staff-schedule/`
  - Respond to Webhook node (returns `{"reply": $json.output}`)
  - System prompt: Sentiri reservation assistant with booking/list/schedule instructions
- **3 critical bugs fixed during n8n setup:**
  1. `$fromAI` shows "undefined" in tool fields — normal, values filled at runtime by LLM
  2. n8n HTTP tools got `ECONNREFUSED ::1:8000` — IPv6 resolution. Fixed by using `0.0.0.0` instead of `localhost` or `127.0.0.1` in tool URLs
  3. DeepSeek model renamed: `deepseek-chat` → `deepseek-flash` (old name = "Bad request" error)
- **Django `chatbot_ask` view rewritten** with smart routing:
  - Booking keywords detected (book, reserve, session, appointment, schedule, available, tempah, jadual, etc.)
  - Booking → POST to n8n webhook `http://localhost:5678/webhook/sentiri-chat` with `{message, client_id, staff_id}`
  - Non-booking → existing RAG pipeline (treatment document Q&A)
  - Returns `routed_to: "n8n_reservation"` or `"rag"` in JSON response
- **End-to-end verified:**
  - Booking question → n8n → AI Agent calls `check_availability` → Django returns `{available: true}` → AI replies "Aina is available, shall I book?" ✅ (2.8s)
  - Treatment question → RAG → retrieves from ChromaDB → generates answer about meltdowns ✅
- **Seed data:** `seed_booking_demo` management command creates StaffSchedule (7 staff × 7 days), StaffTimeOff (1 per staff), 1 sample SessionBooking. Prints cheat-sheet of all IDs.

### What Nik learned
- **n8n = visual orchestration.** Webhook → AI Agent → HTTP tools → response. Same as Django+Celery but visual and language-agnostic.
- **$fromAI() is n8n's tool-parameter binding.** The LLM reads the parameter description, extracts the value from the user's message, and fills it at runtime. Shows "undefined" in the editor — that's expected.
- **IPv6 vs IPv4 killed n8n HTTP tools.** Node.js 17+ resolves `localhost` to `::1` (IPv6) before `127.0.0.1` (IPv4). If Django binds to IPv4 only, the connection is refused. Fix: use `0.0.0.0` which forces IPv4.
- **DeepSeek renamed their models.** `deepseek-chat` → `deepseek-flash`, `deepseek-reasoner` → `deepseek-v4-pro`. Always check `GET /v1/models` before hardcoding model names.
- **Smart routing = one chatbot, two backends.** Keyword detection splits booking questions (→ n8n tool-calling) from treatment questions (→ RAG retrieval). Client sees one chatbot, doesn't know the difference.
- **Django needs `0.0.0.0:8000` for n8n to reach it.** Default `runserver` binds to `127.0.0.1` only. n8n's HTTP tools can't reach it. Start with `python manage.py runserver 0.0.0.0:8000`.

### Architecture diagram (final)
```
[Client types in Sentiri chatbot UI]
       │
       ▼
[Django: chatbot_ask view]
       │
       ├── booking keywords? ──→ [n8n webhook :5678]
       │                              │
       │                         [AI Agent + DeepSeek]
       │                              │
       │                    ┌─────────┼─────────┐
       │                    ▼         ▼         ▼
       │              [check_avail] [book] [list] [schedule]
       │                    │         │         │       │
       │                    └─────────┴─────────┴───────┘
       │                              │
       │                         [Django API :8000]
       │                         [StaffSchedule/TimeOff/Booking]
       │                              │
       │                         [AI generates reply]
       │                              │
       │                    ←─── {reply: "..."}
       │
       └── no booking keywords ──→ [RAG pipeline]
                                     │
                                [ChromaDB retrieval]
                                [Groq LLM generation]
                                     │
                                ←─── {answer: "..."}
```

### What's next
1. ⬜ Activate n8n workflow permanently (production webhook) for reliable testing
2. ⬌ Test full booking flow through actual chatbot UI in browser
3. ⬌ Update progress.md + memory
4. ⬌ Evaluation metrics (sentiment + topic) in separate repo
5. ⬌ Tests + viva sweep
6. ⬌ FYP documentation

## 2026-10-17 (FINAL) — TWO SEPARATE CHATBOTS + n8n RESERVATION COMPLETE ✅

### Final architecture: two distinct chatbots
Split from one mixed chatbot into two clean, separate chatbots:

| | Treatment Assistant 🤖 | Reservation Assistant 📅 |
|---|---|---|
| Nav item | "Ask AI" (blue) | "Reservation" (calendar icon) |
| URL | `/chatbot/` | `/reservation/` |
| View | `chatbot_view` + `chatbot_ask` | `reservation_view` + `reservation_ask` |
| Backend | RAG (ChromaDB + Groq) | n8n webhook → DeepSeek + tool calling |
| Chat bubble color | Blue→Purple gradient | Green→Teal gradient |
| Badge | Blue "X chunks ready" | Green "n8n + DeepSeek" |
| Query log | `ChatQuery.query_type='rag'` | `ChatQuery.query_type='reservation'` |
| Placeholder | "Type your question about autism treatment..." | "Tell me when you want to book a session..." |

### What was changed
- **`ChatQuery` model:** Added `query_type` field (choices: 'rag' / 'reservation'). Migration 0016 applied. Old queries deleted (49 rows).
- **`chatbot_ask` view:** Reverted to pure RAG — no keyword routing, no n8n. Only treatment questions.
- **`reservation_view` + `reservation_ask` views:** New views that route ALL messages to n8n webhook `http://localhost:5678/webhook/sentiri-chat`. Django embeds client_id + staff_id directly in the message: `f"{question}\n\n[Context: client_id={client_id}, staff_id={staff_id}]"`.
- **`reservation.html` template:** Green-themed chat UI, posts to `/reservation/ask/`, separate from treatment chatbot.
- **Client sidebar:** Added "Reservation" nav item between "Ask AI" and "Settings".
- **Simple Memory node added to n8n AI Agent:** Session key = `sentiri-reservation` (static), context window = 15 messages. AI now remembers conversation across messages.
- **Treatment chatbot visual cleanup:** Blue badge (was green), added example placeholder.

### What Nik learned
- **Two chatbots > one smart router.** Keyword-based routing (booking vs RAG) fails on conversational follow-ups ("2026-10-20", "15:00", "yes", "macam mana"). Splitting into two separate chatbots with distinct UIs is cleaner, easier to explain, and has zero routing errors.
- **n8n AI Agent memory.** Simple Memory node stores conversation history locally in n8n. Session ID = `sentiri-reservation` (static for demo). Context window = 15 past messages. Without memory, each webhook call is a fresh conversation — AI forgets "3pm" from message 1 when processing "2026-10-20" in message 2.
- **DeepSeek rate limits.** Free tier = ~60 req/min. AI Agent makes 2+ LLM calls per message (decide → tool → generate). Heavy testing hits the limit fast. Fix: wait 5 minutes.
- **Prompt goes in AI Agent, not Chat Model.** AI Agent node = system prompt + user message + tools. Chat Model node = just API key + model name (engine only).
- **Embed context in the message.** Instead of separate `client_id:` / `staff_id:` lines in the n8n prompt (which show empty because expressions don't resolve), Django embeds them in the message text: `[Context: client_id=10, staff_id=4]`. AI reads it naturally.

### What's next
1. ⬌ End-to-end browser test: Reservation chatbot → full booking flow (DeepSeek rate limit permitting)
2. ⬌ Activate n8n workflow permanently (production webhook toggle)
3. ⬌ Evaluation metrics (sentiment + topic) in separate repo
4. ⬌ Tests + viva sweep
5. ⬌ FYP documentation
6. ⬌ Git commit + push


