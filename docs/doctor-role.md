# Doctor Role — Capabilities & Setup

> What a doctor can do in Sentiri, the pages they see, and the approval workflow.
> Last updated: 2026-10-15

---

## 1. Role Overview

The **Doctor** is a clinical staff member responsible for diagnosing autism and **approving diagnosis documents**. They review uploaded documents (diagnostic reports, psychological evaluations, medical histories) and approve or reject them.

| Capability | Access |
|---|---|
| View own dashboard | ✅ |
| **Approve diagnosis documents** | ✅ |
| See pending documents to review | ✅ |
| See their approved documents | ✅ |
| See their diagnosed clients | ✅ |
| Make/review autism diagnoses | ✅ |
| Manage users / assign clients | ❌ (Admin only) |
| Upload conversations | ❌ (Admin/Therapist only) |

---

## 2. Pages

| URL | Template | Purpose |
|---|---|---|
| `/dashboard/doctor/` | `doctor/doctor_dashboard.html` | Doctor home — pending approvals + diagnosed clients |
| `/dashboard/doctor/approve/<doc_id>/` | `doctor/approve_document.html` | Review + approve a single document |

### Navigation flow
```
Login (doctor role) → /dashboard/doctor/
                          ↓ click "Approve" on a pending doc
                      /dashboard/doctor/approve/<doc_id>/
                          ↓ POST → approve (is_approved=True, approved_by, approval_date)
                      redirect back to /dashboard/doctor/
```

---

## 3. Doctor Dashboard — What It Shows

**KPI Cards (3):**
- **Pending Approvals** — count of documents awaiting review
- **Approved Documents** — count this doctor approved
- **Active Diagnoses** — count of diagnoses this doctor made

**Pending Document Approvals (list):**
Each row shows:
- Document icon + client name + document type
- Uploaded date + who uploaded it
- **View** button (opens the file) + **Approve** button (goes to confirm page)

**My Diagnosed Clients (grid):**
Each card shows:
- Avatar + client name + diagnosis date
- Support level badge (Level 1/2/3)

---

## 4. Approve Document Page — What It Shows

- Client name, document type, upload date, uploaded by
- "View document" link (opens the actual file in a new tab)
- **"✓ Approve Document"** button → POST → sets `is_approved=True`, `approved_by=doctor`, `approval_date=now`
- **Cancel** button → back to dashboard

---

## 5. Backend Logic

### View: `doctor_dashboard`
- `pending_docs` = `DiagnosisDocument.objects.filter(is_approved=False, is_active=True)`
- `approved_docs` = `DiagnosisDocument.objects.filter(is_approved=True, approved_by=doctor)`
- `diagnoses` = `AutismDiagnosis.objects.filter(diagnosed_by=doctor, is_active=True)`

### View: `doctor_approve_document`
- `get_object_or_404(DiagnosisDocument, id=doc_id, is_active=True)`
- On POST: sets `is_approved=True`, `approved_by=request.user`, `approval_date=timezone.now()`
- Redirects back to dashboard with success message

### Security
- Both views decorated with `@doctor_required`
- `approved_by` has `limit_choices_to={'role': 'doctor'}` on the model — only doctors can approve

### URLs (`chat_analyzer/urls.py`)
```python
path("dashboard/doctor/", views.doctor_dashboard, name='doctor_dashboard'),
path("dashboard/doctor/approve/<int:doc_id>/", views.doctor_approve_document, name='doctor_approve_document'),
```

---

## 6. Data Model (`DiagnosisDocument`)

The document that gets approved:

| Field | Type | Purpose |
|---|---|---|
| `client` | FK → User (client) | Whose document |
| `file` | FileField | The actual PDF/image |
| `document_type` | CharField (choices) | diagnostic_report, psychological_eval, etc. |
| `is_approved` | BooleanField | Approval status (the flag being flipped) |
| `approved_by` | FK → User (doctor) | Who approved |
| `approval_date` | DateTimeField | When approved |
| `uploaded_by` | FK → User | Who uploaded |
| `upload_date` | DateTimeField | When uploaded |

---

## 7. Design System Applied

Doctor pages use the same **Apple design system** (`docs/apple-design-system.md`):
- SF Pro font stack + `antialiased`
- `#f5f5f7` background, `#ffffff` cards, 18px radius
- `#0071e3` accent, `#d70015` red (pending), `#1d7a3f` green (approved), `#5e5ce6` purple (level)
- `cubic-bezier(0.25, 0.1, 0.25, 1)` easing
- Staggered `fade-up` animations

**Template-specific classes:**
| Class | Purpose |
|---|---|
| `.d-card` | Flat white card |
| `.d-title` | Page heading |
| `.d-subtitle` | Subtitle |
| `.d-label` | Uppercase small label |
| `.d-pill` | Rounded pill badge |
| `.d-btn` / `.d-btn-secondary` | Approve/cancel buttons |

---

## 8. Testing

**Sample logins** (password reset to `doctor123`):

| Username | Password | Name |
|---|---|---|
| `doctor1` | `doctor123` | Dr. Ahmad Hassan |
| `doctor2` | `doctor123` | Dr. Lisa Wong |

**Verified:**
- ✅ Dashboard returns 200 with 3 KPIs + pending list + diagnosed clients
- ✅ Approve page renders doc details
- ✅ POST approval flips `is_approved=True`, sets `approved_by` + `approval_date`
- ✅ Test approval reverted (data kept clean — 8 pending docs remain)

---

## 9. Future Enhancements

- [ ] Reject flow (with reason) — currently only approve
- [ ] Bulk approve multiple documents
- [ ] Doctor notes on approval
- [ ] Specifier approval (doctors also approve specifiers via `ClientSpecifier`)
- [ ] Notification when a new document awaits review
