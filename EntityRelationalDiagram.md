

erDiagram
    %% ============================================
    %% 1. USER (UNIFIED) - The Core
    %% ============================================
    USER {
        int id PK
        string username UK
        string password
        string email
        string first_name
        string last_name
        string role
        boolean is_active
        boolean is_staff
        boolean is_superuser
        string phone
        date date_of_birth
        string gender
        text address
        string license_number UK
        string license_state
        int years_of_experience
        date hire_date
        string specialization
        string client_status
        datetime last_visit
        datetime last_login
        datetime date_joined
        datetime created_at
        datetime updated_at
        int registered_by_id FK
        int assigned_therapist_id FK
    }

    %% ============================================
    %% 2. AUTISM DIAGNOSIS
    %% ============================================
    AUTISM_DIAGNOSIS {
        int autism_diagnosis_id PK
        int client_id FK
        int diagnosed_by_id FK
        int support_level
        date diagnosis_date
        boolean is_active
        text clinical_notes
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% 3. MASTER SPECIFIER
    %% ============================================
    MASTER_SPECIFIER {
        int specifier_id PK
        string specifier_name UK
        string specifier_category
        boolean is_positive_specifier
        string dsm_code
        boolean is_required
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% 4. CLIENT SPECIFIER (Bridge)
    %% ============================================
    CLIENT_SPECIFIER {
        int client_specifier_id PK
        int autism_diagnosis_id FK
        int specifier_id FK
        string severity
        boolean is_present
        text clinical_notes
        boolean is_initial
        int stated_by_id FK
        date stated_date
        int proposed_by_id FK
        int approved_by_id FK
        boolean is_pending_approval
        boolean is_approved
        date approval_date
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% 5. DOCTOR SPECIALTY (Master Data)
    %% ============================================
    MASTER_SPECIALTY_CATEGORY {
        int category_id PK
        string category_name
        string category_code
        text category_description
        int display_order
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    MASTER_SPECIALTY {
        int specialty_id PK
        string specialty_name
        string specialty_code
        int category_id FK
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    DOCTOR_SPECIALTY {
        int doctor_specialty_id PK
        int doctor_id FK
        int specialty_id FK
        boolean is_board_certified
        date certification_date
        date certification_expires
        boolean is_primary_specialty
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% 6. CONVERSATION (Sentiment Analysis)
    %% ============================================
    CONVERSATION {
        int conversation_id PK
        int client_id FK
        date date
        time time
        string username
        text message
        text cleaned_text
        string sentiment
        datetime uploaded_at
        string upload_batch
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% 7. UNMATCHED MESSAGE
    %% ============================================
    UNMATCHED_MESSAGE {
        int unmatched_id PK
        date date
        time time
        string username
        text message
        datetime uploaded_at
        string upload_batch
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% 8. UPLOAD HISTORY
    %% ============================================
    UPLOAD_HISTORY {
        int upload_id PK
        int admin_id FK
        string file_name
        string batch_id UK
        int message_count
        int matched_count
        int unmatched_count
        string status
        datetime uploaded_at
        int positive_count
        int negative_count
        int neutral_count
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% 9. CLIENT CONTACT
    %% ============================================
    CLIENT_CONTACT {
        int contact_id PK
        int client_id FK
        string contact_type
        string name
        string phone_number
        boolean is_primary
        text notes
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% 10. ADMIN INVITE CODE
    %% ============================================
    ADMIN_INVITE_CODE {
        int invite_id PK
        string code UK
        int created_by_id FK
        datetime expires_at
        int used_by_id FK
        datetime used_at
        string purpose
        text notes
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% 11. DIAGNOSIS DOCUMENT
    %% ============================================
    DIAGNOSIS_DOCUMENT {
        int document_id PK
        int client_id FK
        int uploaded_by_id FK
        string document_type
        string file_name
        string file_path
        int file_size
        string mime_type
        datetime upload_date
        boolean is_verified
        boolean is_approved
        int approved_by_id FK
        datetime approval_date
        text approval_notes
        text rejection_reason
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    %% ============================================
    %% RELATIONSHIPS
    %% ============================================

    %% ===== USER SELF-REFERENCES =====
    USER ||--o{ USER : "registered_by"
    USER ||--o{ USER : "assigned_therapist"

    %% ===== USER → AUTISM DIAGNOSIS =====
    USER ||--o{ AUTISM_DIAGNOSIS : "has (as client)"
    USER ||--o{ AUTISM_DIAGNOSIS : "diagnoses (as doctor)"

    %% ===== AUTISM DIAGNOSIS → CLIENT SPECIFIER =====
    AUTISM_DIAGNOSIS ||--o{ CLIENT_SPECIFIER : "has"

    %% ===== MASTER SPECIFIER → CLIENT SPECIFIER =====
    MASTER_SPECIFIER ||--o{ CLIENT_SPECIFIER : "assigned_to"

    %% ===== USER → CLIENT SPECIFIER (Workflow) =====
    USER ||--o{ CLIENT_SPECIFIER : "states (as doctor)"
    USER ||--o{ CLIENT_SPECIFIER : "proposes (as therapist)"
    USER ||--o{ CLIENT_SPECIFIER : "approves (as doctor)"

    %% ===== DOCTOR SPECIALTY RELATIONSHIPS =====
    MASTER_SPECIALTY_CATEGORY ||--o{ MASTER_SPECIALTY : "contains"
    MASTER_SPECIALTY ||--o{ DOCTOR_SPECIALTY : "has"
    USER ||--o{ DOCTOR_SPECIALTY : "has (as doctor)"

    %% ===== USER → CONVERSATION =====
    USER ||--o{ CONVERSATION : "has (as client)"

    %% ===== USER → UPLOAD HISTORY =====
    USER ||--o{ UPLOAD_HISTORY : "uploads (as admin)"

    %% ===== USER → CLIENT CONTACT =====
    USER ||--o{ CLIENT_CONTACT : "has (as client)"

    %% ===== USER → ADMIN INVITE CODE =====
    USER ||--o{ ADMIN_INVITE_CODE : "creates (as admin)"
    USER ||--o{ ADMIN_INVITE_CODE : "uses (as admin)"

    %% ===== USER → DIAGNOSIS DOCUMENT =====
    USER ||--o{ DIAGNOSIS_DOCUMENT : "has (as client)"
    USER ||--o{ DIAGNOSIS_DOCUMENT : "uploads (as admin/therapist)"
    USER ||--o{ DIAGNOSIS_DOCUMENT : "approves (as doctor)"

## instruction ? just yank this code and paste it into the mermaid.js

#### latest-update: 05 August 2026 
