from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError 
from django.core.validators import RegexValidator
from django.db import models
import uuid
from django.utils import timezone
from datetime import datetime


""" CREATING UNIFIED USER USING AbstractUser """
class User(AbstractUser):
    """ lets unified all roles """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('therapist', 'Therapist'),
        ('doctor', 'Doctor'),
        ('client', 'Client'),
    ]
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='chat_analyzer_user_set',  # ← Unique related_name
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='chat_analyzer_user_set',  # ← Unique related_name
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )
    # defining role .........
    role = models.CharField(
        max_length=20, 
        choices=ROLE_CHOICES, 
        default='client',
        help_text="User's roles in the system"
    )
    # common fields for all users that available
    phone_regex = RegexValidator(
        regex=r'^(\+?60|0)[1-9][0-9]{7,9}$',
        message="phone number must be entered in Malaysian format: 0123456789 or +60123456789"
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        validators=[phone_regex],
        help_text="Enter without spaces (e.g., 0123456789 or +60123456789)"
    )
    date_of_birth = models.DateField(
        blank=True,
        null=True,
        help_text="Date of Birth"
    )

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]

    gender = models.CharField(
        max_length=20,
        choices=GENDER_CHOICES,
        blank=True,
        null=True,
        help_text="Gender Identity"
    )
    address = models.TextField(
        blank=True,
        null=True,
        help_text='Home address'
    )
    # fields for professional ---- (Doctor, Therapist, Admins)
    license_number = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        help_text="professional license number for doctor and therapist"
    )
    license_state = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="State where license is issued"
    )
    years_of_experience = models.IntegerField(
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
   # CLIENT SPECIFIC FIELDS
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
        help_text="Client's status (only for clients fields)"
)
    last_visit = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Date of last visit (only for clients)"
    )

    # ---------- Self-Referential Relationships --------------
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

    # Therapist that assigned to this clients (only for clients)
    assigned_therapist = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_clients',
        limit_choices_to={'role': 'therapist'},
        help_text="Therapist assigned to this client"
    )

    #--- AUDIT FIELDS ---- 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['last_name', 'first_name']
        permissions = [
            ('can_manage_therapist', 'Can manage therapist'),
            ('can_manage_doctors', 'Can manage doctors'),
            ('can_manage_clients', 'Can manage clients'),
            ('can_approve_documents', 'Can approve documents'),
        ]

# -------- String Representation -------- 
    def __str__(self):
        if self.role == 'doctor' and self.first_name:
            return f"Dr. {self.get_full_name()}"
        return self.get_full_name() or self.username

    # we declare the role of properties so that we use it later in our views.py
    # for example we create 
    # 
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
        """Check if user is clinical staff (therapist or doctor)"""
        return self.role in ['therapist', 'doctor']

    @property
    def get_display_name(self):
        """get display name with appropriate title"""
        if self.role == 'doctor' and self.first_name:
            return f"Dr. {self.first_name} {self.last_name}"
        return self.get_full_name() or self.username


    # === CLIENT HELPER property ===
    @property
    def get_primary_contact(self):
        """get the primary contact for this client"""
        if hasattr(self, 'contacts'):
            primary = self.contacts.filter(is_primary=True).first()
            if primary:
                return primary
            return self.contacts.first()
        return None

    @property
    def get_primary_phone(self):
        """get primary contact phone numbers"""
        primary = self.get_primary_contact
        if primary:
            return primary.phone_number
        return self.phone

    @property
    def get_all_phone(self):
        """Get all phones numbers for this client"""
        phones = []
        if self.phone:
            phones.append(self.phone)
        if hasattr(self, 'contacts'):
            for contact in self.contacts.all():
                if contact.phone_number not in phones:
                    phones.append(contact.phone_number)
        return phones

    # ===== VALIDATION SECTION =====
    def clean(self):
        """Custom validation for each model"""
        super().clean() # error before this super.clean(), but both of them must have parentheses
        
        if self.is_superuser:
            return
        # license number is required for doctors and therapist
        if self.role in ['doctor', 'therapist']:
            if not self.license_number:
                raise ValidationError({
                    'license_number': 'license number is required for doctors and therapists.'
                })
            if not self.license_state:
                raise ValidationError({
                    'license_state': 'License state is required fro doctors and therapist'
                })
            
        if self.role in 'client':
            if not self.first_name:
                raise ValidationError({
                    'first_name': "Parent's name is required for clients."
                })
            if not self.last_name:
                raise ValidationError({
                    'last_name': "Child's name is required for clients."
                })

    def save(self, *args, **kwargs):
        """override save to ensure validation tuh clear irrelevant fields"""
        self.full_clean()

        # clear professional fields for non-professionals
        if self.role not in ['doctor', 'therapist']:
            self.license_number = None
            self.license_state = None
            self.years_of_experience = None
            self.hire_date = None
            self.specialization = ''

        # clear client fields for non-clients 
        if self.role != 'client':
            self.client_status = None
            self.last_visit = None
            self.assigned_therapist = None
            # note that: 
        super().save(*args, **kwargs)

#to overcome multiple contact of client
class ClientContact(models.Model):
    """Mutiple contacts for a single client (father, mother, guardian)"""
    CONTACT_TYPES = [
		('father', 'Father'),
		('mother', 'Mother'),
		('guardian', 'Guardian'),
		('other', 'Other'),
	]
	# this is how we connect the Client model
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='contacts',
        limit_choices_to={'role': 'client'},
        help_text="The client this contacts belongs to"
    )
	# another fields
    contact_type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPES,
        help_text="Type of contact such as (father, mother, guardian)"
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
        help_text="is this primary contact"
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
        verbose_name_plural = 'Client Contacts 📇'
        ordering = ['-is_primary', 'contact_type']

    def __str__(self):
        return f"{self.name} ({self.get_contact_type_display()}) - {self.phone_number}"

# ====================================
# client-autism section 😇 03/08/2026
# ====================================
class AutismDiagnosis(models.Model):
    """Autism diagnosis for a client"""

    SUPPORT_LEVEL_CHOICES = [
        (1, 'Level 1 - Requiring Support'),
        (2, 'Level 2 - Requiring Substantial Support'),
        (3, 'Level 3 - Requiring Very Substantial Support'),
    ]

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='autism_diagnoses',
        limit_choices_to={"role": "client"},
        help_text="The client with this diagnosis"
    )

    diagnosed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='diagnoses_made',
        null=True,
        blank=True,
        limit_choices_to={'role': 'doctor'},
        help_text="The doctor who made the diagnosis"
    )

    support_level = models.IntegerField(
        choices=SUPPORT_LEVEL_CHOICES,
        help_text="DSM-5 support level (1,2, or 3)"
    )

    diagnosis_date = models.DateField(
        help_text="date of diagnosis"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Is this the active diagnosis"
    )

    clinical_notes = models.TextField(
        blank=True,
        null=True,
        help_text="additional clinical notes"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Autism Diagnosis'
        verbose_name_plural = 'Autism Diagnoses 💊'
        ordering = ['-diagnosis_date']

    def __str__(self):
        return f"{self.client.get_full_name()} - Level {self.support_level}"

class MasterSpecifier(models.Model):
    """Master list of all possible DSM-5 specifiers. """
    specifier_name = models.CharField(
        max_length=150,
        unique=True,
        help_text="Name of the specifier (e.g., 'With languange impairment ')"
    )
    
    specifier_category = models.CharField(
        max_length=100,
        help_text="Category: Languange, Intellectual, Medical, Behavioral, etc."
    )

    is_positive_specifier = models.BooleanField(
        default=True,
        help_text="TRUE = 'with' (positive), FALSE = 'without' (negative)"
    )

    dsm_code = models.CharField(
        max_length=20,
        blank=True,
        null=True,
        help_text="DSM-5 reference code (e.g., 'DSM-5-01')"
    )
    

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Master Specifier'
        verbose_name_plural = 'Master Specifiers'
        ordering = ['specifier_category', 'specifier_name']

    def __str__(self):
        return self.specifier_name

class ClientSpecifier(models.Model):
    """Bridge table or we called associative entity linking clients to specifiers"""
    SEVERITY_CHOICES = [
        ('mild', 'Mild'),
        ('moderate', 'Moderate'),
        ('severe', 'Severe'),
        ('n/a', 'N/A'),
    ]

    autism_diagnosis = models.ForeignKey(
        AutismDiagnosis,
        on_delete=models.CASCADE,
        related_name='specifiers',
        help_text="the autism diagnosis this specifier belongs to"
    )

    specifier = models.ForeignKey(
        MasterSpecifier,
        on_delete=models.PROTECT,
        related_name='client_specifiers',
        help_text="The specifier from the master list"
    )

    severity = models.CharField(
        max_length=20,
        choices=SEVERITY_CHOICES,
        blank=True,
        null=True,
        help_text="severity level"
    )

    is_present = models.BooleanField(
        default=True,
        help_text="True if client has this specifier, false if client does not have it"
    )

    clinical_notes = models.TextField(
        blank=True,
        null=True,
        help_text="clinical description of how this specifier presents"
    )

    stated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='stated_specifiers',
        null=True,
        blank=True,
        limit_choices_to={'role': 'doctor'},
        help_text="clinician who stated this specifier"
    )

    stated_date = models.DateField(
        null=True,
        blank=True,
        help_text="When this specifier was stated"
    )

    proposed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='proposed_specifiers',
        null=True,
        blank=True,
        limit_choices_to={'role': 'therapist'},
        help_text="Therapist who proposed this specifier"
    )
    
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='approved_specifiers',
        null=True,
        blank=True,
        limit_choices_to={'role': 'doctor'},
        help_text="Clinician who approved this specifier"
    )

    is_pending_approval = models.BooleanField(
        default=False,
        help_text="Is this specifier waiting for approval"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="if dr. directly state this it is already approved but by default it is False until dr. approve "
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Client Specifier'
        verbose_name_plural = 'Client Specifiers'
        unique_together = ('autism_diagnosis', 'specifier')
        ordering = ['-is_present', 'specifier__specifier_category']
    
    def __str__(self):
        status = "Present" if self.is_present else "Absent"
        return f"{self.autism_diagnosis.client.get_full_name()} - {self.specifier.specifier_name} ({status})"

    def clean(self):
        """need to validate if is_present is false then the severity need to be N/A"""
        if not self.is_present and self.severity not in [None, 'n/a']:
            raise ValidationError({
                'severity': 'Severity must be N/A when specifier is not present.'
        })

    def save(self, *args, **kwargs):
        """override save to ensure that validation"""
        self.full_clean()
        super().save(*args, **kwargs)

# =======================================================
# DIAGNOSIS DOCUMENT FOR CLIENT FOR MUCH BETTER WORKFLOWS
# =======================================================
# 5 august 2026 1731H 
class DiagnosisDocument(models.Model):
    """Uploaded diagnostic documents"""
    DOCUMENT_TYPES = [
        ('diagnostic_report', 'Diagnostic Report'),
        ('psychological_eval', 'Psychological Evaluation'),
        ('medical_history', 'Medical History'),
        ('school_report', 'School Report'),
        ('therapy_notes', 'Therapy Notes'),
        ('other', 'Other'),
    ]
    # core fields to connect with client
    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='diagnosis_documents',
        limit_choices_to={'role': 'client'},
        help_text="The client this document belongs to "
    )
    
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='uploaded_documents',
        null=True,
        blank=True,
        help_text="Who uloaded this documents"
    )

    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPES,
        default='diagnostic_report',
        help_text="Type of document"
    )

    file_name = models.CharField(
        max_length=255,
        help_text="Original file name"
    )

    file_path = models.CharField(
        max_length=500,
        help_text="Cloud/S3 path or server path"
    )

    file_size = models.IntegerField(
        blank=True,
        null=True,
        help_text="Size in KB"
    )

    upload_date = models.DateTimeField(auto_now_add=True)

    is_approved = models.BooleanField(
        default=False,
        help_text="Has this document been approved"
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        related_name='approved_documents',
        null=True,
        blank=True,
        limit_choices_to={'role': 'doctor'},
        help_text="Doctor who approved this document"
    )

    approval_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the document was approved"
    )

    # audit fields like always 
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name='Diagnosis Document'
        verbose_name_plural = 'Diagnosis Documents 📑'
        ordering = ['-upload_date']

    def __str__(self):
        return f"{self.client.get_full_name()} - {self.file_name}"


# ====================================
# Dr. Speciality Section (Master Data)
# ====================================
class MasterSpecialtyCategory(models.Model):
    category_name = models.CharField(max_length=100,blank=True, null=True)
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
 

# ** MasterSpecialty **
class MasterSpecialty(models.Model):
    specialty_name = models.CharField(max_length=100,blank=True, null=True)
    specialty_code = models.CharField(max_length=20, blank=True, null=True)
    category = models.ForeignKey(
        MasterSpecialtyCategory,
        on_delete = models.PROTECT,
        related_name = 'specialties',
        null=True,
        blank=True,
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)\

    class Meta:
        verbose_name = 'Doctor Specialty'
        verbose_name_plural = 'All Doctor Specialties Available 🩺 '
        ordering = ['specialty_name']

    def __str__(self):
        return self.specialty_name

# THIS IS THE ASSOCIATIVE TABLE THAT CONNECT BETWEEN {DR AND THEIR SPECIALTY}
class DoctorSpecialty(models.Model):
    """ASSOCIATIVE TABLE ALSO CALLED AS BRIDGE TABLE LINKING DR. TO THEIR SPECIALTIES"""
    doctor = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='doctor_specialties',
        limit_choices_to={'role': 'doctor'},
    )
    specialty = models.ForeignKey(
        MasterSpecialty,
        on_delete = models.PROTECT,
        related_name = 'doctor_specialties',
    )
    # why models protect because we dont want that if Dr. were delete we also delete the specialties
    is_board_certified = models.BooleanField(default=False)
    certification_date = models.DateField(null=True, blank=True)
    certification_expires = models.DateField(null=True, blank=True)
    is_primary_specialty = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('doctor', 'specialty')
        verbose_name = 'Doctor Specialty'
        verbose_name_plural = 'Each Doctor Specialties 🥼'

    def __str__(self):
        return f"{self.doctor} - {self.specialty}"
     
# MODEL NUMB. 4 CONVERSATION
class Conversation(models.Model):

    CHAT_TYPES = [
        ('group', 'Group Chat'),
        ('individual', '1-on-1 Chat'),
        ('admin', 'Admin Chat'),
    ]

    therapist = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='therapist_conversations',
        limit_choices_to={'role': 'therapist'},
        help_text="The therapist involve in this conversation (if therapist sent message)"
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_messages',
        help_text="Who sent this message (client, therapist, or admin)"
    )

    # is this message from client ?
    is_from_client = models.BooleanField(
        default=True,
        help_text="True if message is from client, False if from therapist/staff"
    )

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="conversations",
        help_text="the client this conversation belongs to",
        limit_choices_to={'role': 'client'},
        )

    # in future we can call it by client.coversations.message
    date = models.DateField(help_text="Date of message from whatsapp")
    time = models.TimeField(help_text="Time of the message from whatsapp")
    username = models.CharField(
        max_length=200,
        help_text="original sender name/ number from whatsapp")
    # message section
    message = models.TextField(help_text="original message text")
    # cleaned_text for sentiment analysis (light -cleaning - to preserve the emotions behind the text)
    cleaned_text = models.TextField(
        blank=True,
        null=True,
        help_text='cleaned version (after preprocessing)'
    )
    # for topic modeling ( aggresive cleaning - removes common words )
    cleaned_text_topic = models.TextField(
        blank=True,
        null=True,
        help_text='Cleaned version for topic modeling (aggressive one)'
    )
    # we shall addd to track which cleaning versions is processed
    is_cleaned_sentiment = models.BooleanField(
        default=False,
        help_text="Has this message been cleaned for sentiment analysis ?"
    )

    is_cleaned_topic = models.BooleanField(
        default=False,
        help_text="Has this message been cleaned for topic modeling ??"
    )

    message_hash = models.CharField(
        max_length=64,
        db_index=True,
        unique=True,
        blank=True,
        null=True,
        help_text="use SHA-256 hash for deduplication"
    )
    # analysis result
    sentiment = models.CharField (
        max_length=20,
        blank=True,
        null=True,
        choices=[
            ('positive', 'Positive'),
            ('negative', 'Negative'),
            ('neutral', 'Neutral')
        ],
        help_text='sentiment analysis result'
    )

    sentiment_score = models.FloatField(
        blank=True,
        null=True,
        help_text='Sentiment score from -1.0 to +1.0'
    )

    sentiment_confidence = models.FloatField(
        blank=True,
        null=True,
        help_text='Confidence score from 0.0 to 1.0'
    )
    #meta data: which is the detail about data uploaded
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        help_text="when this was imported"
    )

    upload_batch = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text='Batch ID for grouping uploads'
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_messages',
        help_text="Who uploaded this message"
    )

    # linking with the upload history model
    upload_history = models.ForeignKey(
        'UploadHistory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_messages',
        help_text="The upload batch this message came from"
    )

    # tracking the processing status
    is_processed = models.BooleanField(
        default=False,
        help_text="Has this message has benn processed for analysis"
    )

    chat_type = models.CharField(
        max_length=20,
        choices=CHAT_TYPES,
        default='individual',
        help_text="Type of chat this message came from"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # upload batch needed for better algorithm
    class Meta:
        # kegunaaan verbose name adalah name dkt admin page
        ordering = ['-date', '-time'] # newest first
        verbose_name = "Conversation"
        verbose_name_plural = "Conversations 💬 "
        unique_together = ('client', 'message_hash')
        indexes = [
            models.Index(fields=['client', 'date']),
            models.Index(fields=['sender', 'is_from_client']),
            models.Index(fields=['upload_batch']),
        ]

    # we override the current message save to save it in hash format
    def save(self, *args, **kwargs):
        # auto we hash the message if not present
        if not self.message_hash:
            import hashlib
            text = f"{self.client_id}{self.date}{self.username}{self.message}"

        super().save(*args, **kwargs)

    def __str__(self):
        client_name = self.client.get_full_name() if self.client else "Uknown"
        sender_name = self.sender.get_full_name() if self.sender else self.username
        return f"{self.date} - {client_name}: {self.message[:50]}"
    

# ========================================================================
# =================== UPLOAD HISTORY MODEL 6 ============================
# ========================================================================
class UploadHistory(models.Model):
    """ Track file upload history for audit and reminders"""
    # link to admin who uploaded
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='uploads',
        help_text="Who uploaded this file"
    )

    # file information
    file_name = models.CharField(max_length=255)
    batch_id = models.CharField(
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        db_index=True
    )
    # Statistics
    message_count = models.IntegerField(default=0)
    matched_count = models.IntegerField(default=0)
    unmatched_count = models.IntegerField(default=0)
    duplicate_count = models.IntegerField(default=0)

    # Status for today mate 
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('partial', 'Partial'),
        ('failed', 'Failed'),
        ('processing', 'Processing'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='processing')
    
    # the most important is timestamps
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # 1/6/26 : adding positive_count, negative and neutral count
    positive_count = models.IntegerField(default=0)
    negative_count = models.IntegerField(default=0)
    neutral_count = models.IntegerField(default=0)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Upload History'
        verbose_name_plural = 'Upload Histories 📅 '

    def save(self, *args, **kwargs):
        if not self.batch_id:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
            random_part = uuid.uuid4().hex[:8].upper()
            self.batch_id = f"BATCH_{timestamp}_{random_part}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.file_name} - {self.uploaded_at.strftime('%Y-%m-%d %H:%M')}"

# ========================================================================
# =================== UNMATCHED MESSAGE MODEL 5 ============================
# ========================================================================
class UnmatchedMessage(models.Model):
    """Messages that couldnt be linked to any client"""
    upload_history = models.ForeignKey(
        UploadHistory,
        on_delete=models.CASCADE,
        related_name='unmatched_messages',
        null=True,
        blank=True,
        help_text="The upload batch this message came from"
    )

    # track who uploaded this
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unmatched_messages',
        help_text="Who uploaded this message"
    )

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
        verbose_name_plural = 'Unmatched Messages ❌ '

    def __str__(self):
        return f"{self.date} - {self.username} : {self.message[:50]}"

# ╔════════════════════════════════════════════╗ 
# ║           TOPIC MODELING SECTION           ║ 
# ╚════════════════════════════════════════════╝ 

class Topic(models.Model):
    """Master list of all possible topics that will be generated"""
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Topic name (e.g., 'Kebimbangan')"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of the topic"
    )
    keywords = models.JSONField(
        default=list,
        help_text="List of keywords for this topic (Malay words)"
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics 🧠'
        ordering = ['name']

    def __str__(self):
        return self.name

    
class ClientTopicScore(models.Model):
    """Current topic scores for each client"""

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='topic_scores',
        limit_choices_to={'role': 'client'}
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.PROTECT,
        related_name='client_scores'
    )
    score = models.FloatField(
        default=0.0,
        help_text="Current score for this topic (0.0 to 1.0)"
    )
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('client', 'topic')
        verbose_name = 'Client Topic Score'
        verbose_name_plural = 'Client Topic Scores 📊'
        ordering = ['client', '-score']

    def __str__(self):
        return f"{self.client.get_full_name()} - {self.topic.name}: {self.score:.2f}"

class TopicTrend(models.Model):
    """Daily topic trend data for each client"""

    client = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='topic_trends',
        limit_choices_to={'role': 'client'}
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.PROTECT,
        related_name='trends',
    )
    date = models.DateField(auto_now_add=True)
    score = models.FloatField(
        default=0.0,
        help_text="Score for this topic on this date"
    )
    trend = models.FloatField(
        default=0.0,
        help_text="Trend direction: positive = increasing, negative = decreasing"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('client', 'topic', 'date')
        verbose_name = 'Topic Trend'
        verbose_name_plural = 'Topic Trends 🫀'

class MessageTopic(models.Model):
    """Which topics appear in which messages"""

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='topics'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.PROTECT,
        related_name='message_topics'
    )
    score = models.FloatField(
        help_text="Relevance score this topic"
    )
    confidence = models.FloatField(
        default=0.0,
        help_text="Model confidence (0.0 to 1.0)"
    )
    analyzed_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('conversation', 'topic')
        verbose_name = 'Message Topic'
        verbose_name_plural = 'Message Topics 📜'
        ordering = ['-score']

    def __str__(self):
        return f"{self.conversation.client.get_full_name()} - {self.topic.name}: {self.score:.2f}"


