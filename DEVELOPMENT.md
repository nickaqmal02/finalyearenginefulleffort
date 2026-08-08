# Development Setup Guide

## Prerequisites
- Python 3.12+
- Git
- Virtual environment tool

## Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/project.git
cd project

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
import uuid
from datetime import datetime

# ============================================
# 1. UNIFIED USER MODEL (The Core)
# ============================================

class User(AbstractUser):
    """
    Unified User model for all roles (Admin, Therapist, Doctor, Client).
    This replaces separate Admin, Therapist, Doctor, and Client models.
    """

    # ---------- Role Definition ----------
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('therapist', 'Therapist'),
        ('doctor', 'Doctor'),
        ('client', 'Client'),
    ]

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='client',
        help_text="User's role in the system"
    )

    # ---------- Personal Information ----------
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[phone_regex],
        help_text="Contact phone number"
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="Date of birth"
    )

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('non_binary', 'Non-Binary'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer Not to Say'),
    ]
    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        help_text="Gender identity"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text="Home address"
    )

    # ---------- Professional Fields (for Doctors, Therapists, Admins) ----------
    license_number = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="Professional license number (for doctors and therapists)"
    )
    license_state = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="State where license is issued"
    )
    years_of_experience = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Years of professional experience"
    )
    hire_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date of hire"
    )
    specialization = models.CharField(
        max_length=200,
        blank=True,
        help_text="Primary specialization"
    )

    # ---------- Client-Specific Fields ----------
    # Note: first_name = Parent's name, last_name = Child's name (for clients)

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]
    client_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        blank=True,
        null=True,
        help_text="Client's status (only for clients)"
    )
    last_visit = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date of last visit (only for clients)"
    )

    # ---------- Self-Referential Relationships ----------
    # Admin who registered this user (works for Clients, Therapists, Doctors)
    registered_by = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='registered_users',
        limit_choices_to={'role': 'admin'},
        help_text="Admin who registered this user"
    )

    # Therapist assigned to this client (only for clients)
    assigned_therapist = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients',
        limit_choices_to={'role': 'therapist'},
        help_text="Therapist assigned to this client"
    )

    # ---------- Audit Fields ----------
    # is_active, last_login, date_joined are inherited from AbstractUser
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ---------- Meta Class ----------
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['last_name', 'first_name']
        permissions = [
            ('can_generate_invite_code', 'Can generate admin invite codes'),
            ('can_revoke_invite_code', 'Can revoke admin invite codes'),
            ('can_manage_therapists', 'Can manage therapists'),
            ('can_manage_doctors', 'Can manage doctors'),
            ('can_manage_clients', 'Can manage clients'),
            ('can_approve_documents', 'Can approve clinical documents'),
        ]

    # ---------- String Representation ----------
    def __str__(self):
        if self.role == 'doctor' and self.first_name:
            return f"Dr. {self.get_full_name()}"
        return self.get_full_name() or self.username

    # ---------- Role Check Properties ----------
    @property
    def is_admin(self):
        return self.role == 'admin'

    @property
    def is_therapist(self):
        return self.role == 'therapist'

    @property
    def is_doctor(self):
        return self.role == 'doctor'

    @property
    def is_client(self):
        return self.role == 'client'

    @property
    def is_clinical_staff(self):
        """Check if user is clinical staff (therapist or doctor)."""
        return self.role in ['therapist', 'doctor']

    @property
    def get_display_name(self):
        """Get display name with appropriate title."""
        if self.role == 'doctor' and self.first_name:
            return f"Dr. {self.first_name} {self.last_name}"
        return self.get_full_name() or self.username

    # ---------- Client Helpers ----------
    @property
    def get_primary_contact(self):
        """Get the primary contact for this client."""
        if hasattr(self, 'contacts'):
            primary = self.contacts.filter(is_primary=True).first()
            if primary:
                return primary
            return self.contacts.first()
        return None

    @property
    def get_primary_phone(self):
        """Get primary contact phone number."""
        primary = self.get_primary_contact
        if primary:
            return primary.phone_number
        return self.phone

    @property
    def get_all_phones(self):
        """Get all phone numbers for this client."""
        phones = []
        if self.phone:
            phones.append(self.phone)
        if hasattr(self, 'contacts'):
            for contact in self.contacts.all():
                if contact.phone_number not in phones:
                    phones.append(contact.phone_number)
        return phones

    # ---------- Validation ----------
    def clean(self):
        """Custom validation for the model."""
        super().clean()

        # License number is required for doctors and therapists
        if self.role in ['doctor', 'therapist']:
            if not self.license_number:
                raise ValidationError({
                    'license_number': 'License number is required for doctors and therapists.'
                })
            if not self.license_state:
                raise ValidationError({
                    'license_state': 'License state is required for doctors and therapists.'
                })

        # Parent/Child names are required for clients
        if self.role == 'client':
            if not self.first_name:
                raise ValidationError({
                    'first_name': "Parent's name is required for clients."
                })
            if not self.last_name:
                raise ValidationError({
                    'last_name': "Child's name is required for clients."
                })

    def save(self, *args, **kwargs):
        """Override save to ensure validation and clear irrelevant fields."""
        self.full_clean()

        # Clear professional fields for non-professionals
        if self.role not in ['doctor', 'therapist']:
            self.license_number = None
            self.license_state = None
            self.years_of_experience = None
            self.hire_date = None
            self.specialization = ''

        # Clear client fields for non-clients
        if self.role != 'client':
            self.client_status = None
            self.last_visit = None
            self.assigned_therapist = None
            # Note: registered_by can still track who created this user

        super().save(*args, **kwargs)


# ============================================
# 2. CLIENT CONTACT (Stays Exactly the Same)
# ============================================

class ClientContact(models.Model):
    """Multiple contacts for a single client (father, mother, guardian)."""

    CONTACT_TYPES = [
        ('father', 'Father'),
        ('mother', 'Mother'),
        ('guardian', 'Guardian'),
        ('other', 'Other'),
    ]

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contacts',
        limit_choices_to={'role': 'client'},
        help_text="The client this contact belongs to"
    )
    contact_type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPES,
        help_text="Type of contact (father, mother, guardian, etc.)"
    )
    name = models.CharField(
        max_length=200,
        help_text="Full name of the contact"
    )
    phone_number = models.CharField(
        max_length=20,
        help_text="Contact phone number"
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Is this the primary contact?"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about this contact"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Client Contact'
        verbose_name_plural = 'Client Contacts'
        ordering = ['-is_primary', 'contact_type']

    def __str__(self):
        return f"{self.name} ({self.get_contact_type_display()}) - {self.phone_number}"

    def save(self, *args, **kwargs):
        """Ensure only one primary contact per client."""
        if self.is_primary:
            ClientContact.objects.filter(
                client=self.client,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)


# ============================================
# 3. DOCTOR SPECIALTY (Master Data)
# ============================================

class MasterSpecialtyCategory(models.Model):
    """Categories for specialties (e.g., 'Psychiatry')."""
    category_name = models.CharField(max_length=100, blank=True, null=True)
    category_code = models.CharField(max_length=20, blank=True, null=True)
    category_description = models.TextField(blank=True, null=True)
    display_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Doctor Specialty Category'
        verbose_name_plural = 'Doctor Specialty Categories'
        ordering = ['display_order', 'category_name']

    def __str__(self):
        return self.category_name or "Unnamed Category"


class MasterSpecialty(models.Model):
    """Master list of all medical specialties (e.g., 'Child Psychiatry')."""
    specialty_name = models.CharField(max_length=100, blank=True, null=True)
    specialty_code = models.CharField(max_length=20, blank=True, null=True)
    category = models.ForeignKey(
        MasterSpecialtyCategory,
        on_delete=models.PROTECT,
        related_name='specialties',
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Master Specialty'
        verbose_name_plural = 'Master Specialties'
        ordering = ['specialty_name']

    def __str__(self):
        return self.specialty_name or "Unnamed Specialty"


class DoctorSpecialty(models.Model):
    """Bridge table linking doctors to their specialties."""
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_specialties',
        limit_choices_to={'role': 'doctor'},
    )
    specialty = models.ForeignKey(
        MasterSpecialty,
        on_delete=models.PROTECT,
        related_name='doctor_specialties',
    )
    is_board_certified = models.BooleanField(default=False)
    certification_date = models.DateField(null=True, blank=True)
    certification_expires = models.DateField(null=True, blank=True)
    is_primary_specialty = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('doctor', 'specialty')
        verbose_name = 'Doctor Specialty'
        verbose_name_plural = 'Doctor Specialties'

    def __str__(self):
        return f"{self.doctor.get_display_name} - {self.specialty}"


# ============================================
# 4. CONVERSATION (For Sentiment Analysis)
# ============================================

class Conversation(models.Model):
    """Chat messages for sentiment analysis."""
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations',
        limit_choices_to={'role': 'client'},
        help_text="The client this conversation belongs to"
    )
    date = models.DateField(help_text="Date of message from WhatsApp")
    time = models.TimeField(help_text="Time of the message from WhatsApp")
    username = models.CharField(
        max_length=200,
        help_text="Original sender name/number from WhatsApp"
    )
    message = models.TextField(help_text="Original message text")
    cleaned_text = models.TextField(
        blank=True,
        null=True,
        help_text="Cleaned version (after preprocessing)"
    )
    SENTIMENT_CHOICES = [
        ('positive', 'Positive'),
        ('negative', 'Negative'),
        ('neutral', 'Neutral'),
    ]
    sentiment = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        choices=SENTIMENT_CHOICES,
        help_text="Sentiment analysis result"
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When this was imported"
    )
    upload_batch = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Batch ID for grouping uploads"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations"

    def __str__(self):
        client_name = self.client.get_full_name() or "Unknown"
        return f"{self.date} - {client_name}: {self.message[:50]}"


# ============================================
# 5. UNMATCHED MESSAGE
# ============================================

class UnmatchedMessage(models.Model):
    """Messages that couldn't be linked to any client."""
    date = models.DateField()
    time = models.TimeField()
    username = models.CharField(max_length=200)
    message = models.TextField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    upload_batch = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']
        verbose_name = 'Unmatched Message'
        verbose_name_plural = 'Unmatched Messages'

    def __str__(self):
        return f"{self.date} - {self.username}: {self.message[:50]}"


# ============================================
# 6. UPLOAD HISTORY
# ============================================

class UploadHistory(models.Model):
    """Track file upload history for audit and reminders."""
    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploads',
        limit_choices_to={'role': 'admin'},
    )
    file_name = models.CharField(max_length=255)
    batch_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        db_index=True
    )
    message_count = models.IntegerField(default=0)
    matched_count = models.IntegerField(default=0)
    unmatched_count = models.IntegerField(default=0)

    STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='success'
    )

    positive_count = models.IntegerField(default=0)
    negative_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)

    uploaded_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Upload History'
        verbose_name_plural = 'Upload Histories'

    def save(self, *args, **kwargs):
        if not self.batch_id:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            random_part = uuid.uuid4().hex[:8].upper()
            self.batch_id = f"BATCH_{timestamp}_{random_part}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"


# ============================================
# 7. ADMIN INVITE CODE (Optional but Recommended)
# ============================================

class AdminInviteCode(models.Model):
    """Secure admin invitation codes with expiration and tracking."""
    code = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="The invitation code"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_invites',
        limit_choices_to={'role': 'admin'},
        help_text="Who created this invite"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        help_text="When this code expires"
    )
    used_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='used_invites',
        help_text="Who used this code"
    )
    used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When this code was used"
    )
    PURPOSE_CHOICES = [
        ('admin_registration', 'Admin Registration'),
        ('therapist_invite', 'Therapist Invite'),
        ('doctor_invite', 'Doctor Invite'),
    ]
    purpose = models.CharField(
        max_length=50,
        choices=PURPOSE_CHOICES,
        default='admin_registration'
    )
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Admin Invite Code'
        verbose_name_plural = 'Admin Invite Codes'

    def __str__(self):
        status = "Used" if self.used_by else "Active"
        return f"{self.code[:8]}... ({status})"

    @property
    def is_expired(self):
        """Check if the code has expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at

    @property
    def is_usable(self):
        """Check if the code can still be used."""
        return self.is_active and not self.is_expired and not self.used_by

    def use(self, user):
        """Mark the code as used by a user."""
        if not self.is_usable:
            raise ValueError("This invite code is no longer usable.")
        self.used_by = user
        self.used_at = timezone.now()
        self.save()

    @classmethod
    def generate_code(cls):
        """Generate a secure, human-readable code."""
        import random
        import string

        def random_segment(length=5):
            return ''.join(random.choices(
                string.ascii_uppercase + string.digits,
                k=length
            ))

        return f"AUT-{random_segment()}-{random_segment()}"

    @classmethod
    def create_invite(cls, created_by=None, hours_valid=72, purpose='admin_registration'):
        """Create a new invite code."""
        from django.utils import timezone
        expires_at = timezone.now() + timedelta(hours=hours_valid)

        code = cls.generate_code()
        while cls.objects.filter(code=code).exists():
            code = cls.generate_code()

        return cls.objects.create(
            code=code,
            created_by=created_by,
            expires_at=expires_at,
            purpose=purpose,
            is_active=True
        )

