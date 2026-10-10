# MVP Gap Analysis — Sentiri vs Proposal

> Generated: 2026-10-07
> Source: `PROPOSAL_NICK_new.pdf` (LAMPIRAN A UPNM.PSM.1/2024)
> Auditor: Hermes Agent (codebase-verified, not self-reported)

---

## ✅ COMPLETED — Proposal promises that ARE in the codebase

| Proposal scope | Codebase evidence | Status |
|---|---|---|
| **1. User Management Module** — Registration, auth, profile, RBAC | `models.py` User model with 4 roles (admin/therapist/doctor/client), custom permissions, `admin.py` CustomUserAdmin | ✅ Done |
| **2. WhatsApp Chat Import Module** — Upload, parse, phone detection, client matching | `whatsapp_parser.py`, `upload_service.py`, `upload_chats.py` command, `UploadChatsView` admin view | ✅ Done |
| **3. Phone Number Detection + Client Matching** | `ClientContact` model, `_find_sender()` in upload_service, `phone_to_user` dict matching | ✅ Done |
| **4. Unmatched Messages Storage** | `UnmatchedMessage` model exists | ✅ Done |
| **5. Batch Processing** | `upload_batch` field on Conversation model | ✅ Done |
| **6. Sentiment Analysis Module** — XLM-R, positive/negative/neutral | `sentiment_analyzer.py` (MalaySentimentAnalyzer), XLM-R label mapping (0=neg, 1=neu, 2=pos) | ✅ Done |
| **7. Topic Modeling Module** — BERTopic, XLM-R embeddings, clustering | `topic_modeler.py` (732 LOC), `topic_mapper.py` (191 LOC), three-door cascade (coverage + cluster + outlier) | ✅ Done |
| **8. Admin Dashboard** — Interactive dashboard with charts | `dashboard.py` (dashboard_callback), `templates/admin/index.html` with KPI cards, doughnut chart, radar chart, cohort table | ✅ Done |
| **9. Reporting Module (partial)** — Client progress, sentiment trends, topic insights | `ClientTopicScore` model, `TopicTrend` model, cohort table on admin dashboard | ✅ Done |
| **10. Multilingual NLP** — Bahasa Malaysia, English, Manglish | XLM-R supports Malay natively, `malay_normalizer.py`, `text_cleaner.py` with Sastrawi stemming, dual cleaning (sentiment + topic) | ✅ Done |
| **11. DSM-5 Diagnosis** — Support levels 1/2/3, specifiers | `AutismDiagnosis` model, `MasterSpecifier`, `ClientSpecifier` bridge table, custom admin forms | ✅ Done |
| **12. Diagnosis Documents** — Upload clinical PDFs/images | `DiagnosisDocument` model with `FileField`, `UploadDocumentView` custom admin view, FileExtensionValidator | ✅ Done |
| **13. Fine-tuned XLM-R** | `fine_tune_sentiment.py` exists | ✅ Done |
| **14. Django Admin Panel** — User and model management | Full admin config with unfold theme, custom views, autocomplete_fields | ✅ Done |
| **15. CSRF tokens** — Data security | Django's built-in CSRF middleware, `{% csrf_token %}` in all templates | ✅ Done |

---

## ❌ MISSING — Proposal promises NOT in the codebase

| Proposal scope | What's promised | What's missing | Priority |
|---|---|---|---|
| **1. DRF API Endpoints** | Not explicitly in proposal, but implied by "modular architecture allowing for future feature additions" and "scalability" | No `serializers.py`, no DRF views, no API endpoints. Only admin panel exists. | 🔴 HIGH (for Deloitte reapply) |
| **2. Client-facing read-only dashboard** | "Client: Can view their own diagnosis, support level, sentiment analysis results, and topic insights. Clients can track their own progress in a read-only dashboard." | No client-facing template/view. Admin dashboard exists, but clients can't log in to see their own data. | 🔴 HIGH (proposal explicitly promises this) |
| **3. Therapist dashboard** | "Therapists can view only their assigned clients and monitor their sentiment trends and topic patterns over time." | No therapist-specific view. Admin dashboard shows ALL clients. No per-therapist filtering. | 🔴 HIGH (proposal explicitly promises this) |
| **4. Doctor diagnostic view** | "Doctors have diagnostic authority to add and update clinical data." | Doctor can access admin, but no doctor-specific dashboard. No filtered view of their diagnosed clients. | 🟡 MEDIUM |
| **5. Reporting Module (full)** | "Interactive dashboard showing client progress, sentiment trends, and topic insights for therapists and clients." | Admin dashboard has charts, but NO per-client detail page with trend over time. `TopicTrend` model exists but 0 rows populated. | 🟡 MEDIUM |
| **6. Sentiment trend over time** | "track individual client progress over time based on their conversation patterns" | `TopicTrend` model exists (score + trend per date), but no view/template renders it. No Chart.js line chart for trend. | 🟡 MEDIUM |
| **7. Per-client topic insights** | "topic insights for therapists and clients" | Admin dashboard shows aggregate cohort, but no per-client drill-down showing "this client's topics + sentiments" | 🟡 MEDIUM |
| **8. System evaluation / testing** | "To test and evaluate the functionality of Sentiri and the performance of its sentiment analysis and topic modeling components." | No test suite. No `tests.py` with meaningful tests. No evaluation metrics (accuracy, F1, coherence scores). | 🟡 MEDIUM (viva requirement) |

---

## ⚠️ PARTIALLY DONE — Exists but incomplete

| Feature | What exists | What's missing | Priority |
|---|---|---|---|
| **Topic quality (Run 8)** | BERTopic pipeline runs, 124/124 conversations covered | 3/9 discovered topics are garbage (`buka-nangis-baru`, `child-has-the`, `menangis tidur-mampu-suka bagus`) | 🔴 HIGH (demo-critical) |
| **Signal guard verification** | `signals.py` has `if instance.topic.status != 'active': return` guard | Never live-tested (Path B — deferred) | 🟡 MEDIUM (viva risk) |
| **ClientTopicScore recompute** | Trigger inside `train_topics` command (verified: 42 pairs) | Only fires on retrain. No signal on Topic promotion (Policy C step 2 deferred) | 🟢 LOW (works for demo) |
| **RBAC enforcement** | User model has roles + permissions. Admin has `permission_required` on custom views. | No view-level filtering (therapist sees ALL clients, not just assigned ones). Admin-only enforcement. | 🟡 MEDIUM (proposal promises per-role views) |
| **Batch processing UI** | `upload_batch` field exists on Conversation | No admin UI to filter/group by batch. No batch history view. | 🟢 LOW |

---

## 📋 MVP COMPLETION CHECKLIST — Ordered by priority

### 🔴 P0 — Demo-critical (must fix before any presentation)

- [ ] **Run 8: Kill garbage topics** — Fix `text_cleaner.py` (English stopwords), fix `topic_modeler.py` c-TF-IDF keyword extraction, re-train. Target: 0 jammed topic names, 0 English leaks.
- [ ] **Viva sweep: Run 7-print signal guard test** — Verify `if instance.topic.status != 'active': return` actually skips discovered topics.
- [ ] **Client-facing dashboard** — Create `/dashboard/client/<id>/` view showing: diagnosis, topic scores, sentiment breakdown, recent conversations. Read-only. `{% extends "base.html" %}`.
- [ ] **Therapist dashboard** — Create `/dashboard/therapist/` view showing: assigned clients only, sentiment trends, topic patterns. Filter by `Conversation.therapist == request.user`.

### 🟡 P1 — Proposal promises (must exist for viva defense)

- [ ] **Per-client detail page** — Drill-down from admin dashboard card. Shows individual client's topic × sentiment breakdown, trend over time.
- [ ] **TopicTrend population** — Wire `TopicTrend` computation (either signal or command). Populate rows. Render as Chart.js line chart.
- [ ] **RBAC view-level enforcement** — Therapist sees only assigned clients. Doctor sees only diagnosed clients. Client sees only own data.
- [ ] **Test suite** — At minimum: `test_whatsapp_parser.py`, `test_sentiment_analyzer.py`, `test_topic_modeler.py`. Even basic smoke tests.
- [ ] **Evaluation metrics** — Sentiment accuracy on labeled data. Topic coherence score (c-TF-IDF). Document in a notebook.

### 🟢 P2 — Nice-to-have (strengthens but not blocking)

- [ ] **DRF API endpoints** — `serializers.py` + `views.py` with topics, conversations, messages endpoints. Role-based permissions. (Deloitte reapply strength)
- [ ] **Doctor dashboard** — Filtered view of diagnosed clients.
- [ ] **Batch history UI** — Admin can filter conversations by `upload_batch`, view batch stats.
- [ ] **Fix README** — Broken LinkedIn link (`yourusername` → real URL). Remove React/DRF/FastAPI badges until code exists.
- [ ] **Policy C step 2** — Topic promotion signal (pre_save + post_save on Topic.status). Currently deferred — recompute only fires on retrain.

---

## 📊 SUMMARY

| Category | Count |
|---|---|
| ✅ Completed | 15 features |
| ❌ Missing | 8 features |
| ⚠️ Partially done | 5 features |
| 🔴 P0 (demo-critical) | 4 items |
| 🟡 P1 (viva defense) | 5 items |
| 🟢 P2 (nice-to-have) | 5 items |

**MVP completion: ~65% of proposal scope delivered.** Core NLP pipeline + admin tooling + clinical models are done. Missing: client/therapist-facing dashboards, RBAC enforcement at view level, test suite, topic quality cleanup.

---

## 🗓️ RECOMMENDED BUILD ORDER

```
Week 1 (Oct 7-13):   Run 8 garbage cleanup + Viva sweep (P0)
Week 2 (Oct 14-20):  Client dashboard + Therapist dashboard (P0)
Week 3 (Oct 21-27):  Per-client detail + TopicTrend + RBAC (P1)
Week 4 (Oct 28-Nov 3): Tests + Evaluation metrics (P1)
Week 5+ (Nov 4+):    DRF + Doctor dashboard + Polish (P2)
```

**Demo day estimate: early November.** 5-6 weeks of focused work.
