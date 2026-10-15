# Therapist Role — Capabilities & Setup

> What a therapist can do in Sentiri, the pages they see, and the design system applied.
> Last updated: 2026-10-15

---

## 1. Role Overview

The **Therapist** is a clinical staff member who works directly with assigned clients. They monitor client progress, review sentiment trends, and understand each client's therapeutic journey — but they **cannot** manage other users, upload chats, or approve diagnoses (that's the Admin/Doctor's domain).

| Capability | Access |
|---|---|
| View own dashboard | ✅ |
| View assigned clients | ✅ |
| Drill into a client's progress | ✅ |
| See sentiment breakdown per client | ✅ |
| See topic breakdown per client | ✅ |
| See recent messages | ✅ |
| **Upload WhatsApp .txt for own clients** | ✅ |
| Manage users / assign clients | ❌ (Admin only) |
| Approve documents / diagnoses | ❌ (Doctor only) |
| Upload conversations for any client | ❌ (only their assigned clients) |

---

## 2. Pages

| URL | Template | Purpose |
|---|---|---|
| `/dashboard/therapist/` | `MainTherapist/dashboard.html` | Therapist home — KPIs + assigned client cards |
| `/dashboard/therapist/client/<id>/` | `MainTherapist/ClientTherapist/client_detail.html` | Single client's full progress view |
| `/dashboard/therapist/upload/` | `MainTherapist/upload_chat.html` | Upload WhatsApp .txt for assigned clients |

### Navigation flow
```
Login (therapist role) → /dashboard/therapist/
                              ↓ click a client card
                         /dashboard/therapist/client/<id>/
                              ↓ "← Back to Dashboard"
                         /dashboard/therapist/
```

---

## 3. Therapist Dashboard — What It Shows

**KPI Cards (4):**
- **My Clients** — count of active assigned clients
- **Total Messages** — messages across all assigned clients (with sentiment)
- **Positive Messages** — positive sentiment count
- **Avg Sentiment** — mean sentiment score

**Assigned Client Cards (grid):**
Each card shows:
- Avatar (initials) + full name + phone
- Support level badge (if diagnosed)
- Positive % and negative % pills
- Total message count + last message date
- Click → drills into client detail

---

## 4. Client Detail Page — What It Shows

**KPI Cards (4):**
- Total messages
- Positive count
- Negative count
- Support level

**Sections:**
1. **Diagnosis** — DSM-5 support level + specifiers (present/absent pills)
2. **Sentiment Progress** — Chart.js line chart (Apple blue)
3. **Topic Breakdown** — progress bars per topic
4. **Recent Messages** — last 10 messages, color-coded by client/therapist + sentiment

---

## 5. Backend Logic

### View: `therapist_dashboard`
- Fetches `request.user.assigned_clients` (filtered `is_active=True`)
- For each client: aggregates sentiment (positive/negative/neutral), total count, diagnosis level, last message
- Computes aggregate stats across all assigned clients

### View: `therapist_upload_chat`
- Uses `TherapistUploadChatForm` (client field scoped to `assigned_therapist=request.user`)
- `chat_type` field offers all 3 options: `individual`, `group`, `admin`
- The `therapist` field is auto-set to `request.user` (no self-pick)
- Calls `process_whatsapp_upload()` → then `train_topics()` for retraining

### View: `therapist_client_detail`
- Fetches a client scoped to `assigned_therapist=request.user` (security: therapist can only see their own clients)
- Builds sentiment progress chart data (daily `Sum(sentiment_score)`)
- Fetches topics, diagnosis, specifiers, recent 10 messages

### Security
- All views decorated with `@therapist_required`
- Client detail uses `get_object_or_404(..., assigned_therapist=therapist)` — prevents cross-therapist access
- Upload form scopes `client` queryset to assigned clients — can't upload for others

### URLs (`chat_analyzer/urls.py`)
```python
path("dashboard/therapist/", views.therapist_dashboard, name='therapist_dashboard'),
path("dashboard/therapist/client/<int:client_id>/", views.therapist_client_detail, name='therapist_client_detail'),
path("dashboard/therapist/upload/", views.therapist_upload_chat, name='therapist_upload_chat'),
```

---

## 6. Design System Applied

Therapist pages use the same **Apple design system** as the rest of Sentiri (see `docs/apple-design-system.md`):

- SF Pro font stack + `antialiased`
- `#f5f5f7` background, `#ffffff` cards with 18px radius
- `#1d1d1f` titles, `#6e6e73` secondary, `#86868b` labels
- `#0071e3` accent (Apple blue), `#34c759` green, `#d70015` red
- `cubic-bezier(0.25, 0.1, 0.25, 1)` easing on all transitions
- Pill badges with 980px radius
- Staggered `fade-up` entrance animations

**Template-specific classes** (defined in each template's `{% block extra_css %}`):
| Class | Purpose |
|---|---|
| `.t-card` | Flat white card with layered shadow |
| `.t-title` | Page heading |
| `.t-subtitle` | Subtitle |
| `.t-label` | Uppercase small label |
| `.t-pill` | Rounded pill badge |
| `.t-avatar` | Circular avatar |
| `.t-bar-track` / `.t-bar-fill` | Progress bar |

---

## 7. Testing

To test as a therapist, log in with a therapist account (e.g. `therapist3` / `Farah Ismail`, 2 assigned clients).

**Verified:**
- ✅ Dashboard returns 200 with all 4 KPIs + client cards
- ✅ Client detail returns 200 with chart, topics, recent messages
- ✅ Security: therapist can only access their assigned clients

---

## 8. Future Enhancements

- [ ] Message-level sentiment timeline (per-message, not just daily aggregate)
- [ ] Therapist notes/annotations on clients
- [ ] Alerts for clients with declining sentiment
- [ ] Export client progress report (PDF)
