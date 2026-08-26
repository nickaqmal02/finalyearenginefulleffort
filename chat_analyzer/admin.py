from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm, CustomUserChangeForm 
import csv
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from .models import(
    User,
    ClientContact,
    AutismDiagnosis,
    MasterSpecifier,
    ClientSpecifier,
    DiagnosisDocument,
    MasterSpecialtyCategory,
    MasterSpecialty,
    DoctorSpecialty,
    Conversation,
    UnmatchedMessage,
    UploadHistory,
    Topic,
    ClientTopicScore,
    TopicTrend,
    MessageTopic,
)

User = get_user_model()

try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass
# ===================
# 1. USER ADMIN (CUSTOM)
# ===================
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Custom User admin with all fields."""
    
    # ✅ Use custom forms
    add_form = CustomUserCreationForm
    form = CustomUserChangeForm
    
    list_display = [
        'username',
        'email',
        'first_name',
        'last_name',
        'role',
        'is_active',
        'is_staff',
        'is_superuser',
        'date_joined'
    ]
    
    list_filter = ['role', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    # Fields for vieing/editing
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Information', {
            'fields': (
                'first_name',
                'last_name',
                'email',
                'phone',
                'date_of_birth',
                'gender',
                'address'
            )
        }),
        ('Role & Permissions', {
            'fields': (
                'role',
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            )
        }),
        ('Professional Information', {
            'fields': (
                'license_number',
                'license_state',
                'years_of_experience',
                'hire_date',
                'specialization'
            ),
            'classes': ('collapse',)
        }),
        ('Client Information', {
            'fields': (
                'client_status',
                'last_visit',
                'registered_by',
                'assigned_therapist'
            ),
            'classes': ('collapse',)
        }),
        ('Important Dates', {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    # Fields for adding
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username',
                'password1',
                'password2',
                'role',
                'first_name',
                'last_name',
                'email',
                'phone',
                'date_of_birth',
                'gender',
                'address',
                'license_number',
                'license_state',
                'years_of_experience',
                'hire_date',
                'specialization',
                'client_status',
                'registered_by',
                'assigned_therapist',
                'is_active',
                'is_staff',
                'is_superuser',
            ),
        }),
    )

    # kita override the formfield for 
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Filter foreign key fields in the admin"""
        if db_field.name == 'registered_by':
            kwargs['queryset'] = User.objects.filter(role='admin', is_active=True)
        
        elif db_field.name == 'assigned_therapist':
            kwargs['queryset'] = User.objects.filter(role='therapist', is_active=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# ╔════════════════════════════════════════════╗ 
# ║             2. CLIENT CONTACT              ║ 
# ╚════════════════════════════════════════════╝ 

@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    list_display = ['name', 'client', 'contact_type', 'phone_number', 'is_primary']
    list_filter = ['contact_type', 'is_primary']
    search_fields = ['name', 'phone_number', 'client__first_name', 'client__last_name']
    raw_id_fields = ['client']


# ╔════════════════════════════════════════════╗ 
# ║            3. AUTISM DIAGNOSIS             ║ 
# ╚════════════════════════════════════════════╝ 

@admin.register(AutismDiagnosis)
class AutismDiagnosisAdmin(admin.ModelAdmin):
    list_display = ['client', 'support_level', 'diagnosis_date', 'diagnosed_by', 'is_active']
    list_filter = ['support_level', 'is_active', 'diagnosis_date']
    search_fields = ['client__first_name', 'client__last_name', 'diagnosed_by__username']
    raw_id_fields = ['client', 'diagnosed_by']
    data_hierarchy = 'diagnosis_date'


# ╔════════════════════════════════════════════╗ 
# ║    4.  MASTER SPECIFIER : SLEEP ISSUES     ║ 
# ╚════════════════════════════════════════════╝ 

@admin.register(MasterSpecifier)
class MasterSpecifierAdmin(admin.ModelAdmin):
    list_display = ['specifier_name', 'specifier_category', 'is_positive_specifier', 'is_active']
    list_filter = ['specifier_category', 'is_positive_specifier', 'is_active']
    search_fields = ['specifier_name', 'dsm_code']
    ordering = ['specifier_category', 'specifier_name']


# ╔════════════════════════════════════════════╗ 
# ║    5. CLIENT DETAIL SPECIFIER ASSOCIATE    ║ 
# ╚════════════════════════════════════════════╝ 
#
@admin.register(ClientSpecifier)
class ClientSpecifierAdmin(admin.ModelAdmin):
    list_display=[
        'autism_diagnosis',
        'specifier',
        'is_present',
        'severity',
        'is_pending_approval',
        'is_approved'
    ]
    list_filter = ['is_present', 'severity', 'is_pending_approval', 'is_approved']
    search_fields = ['autism_diagnosis__client__first_name', 'specifier__specifier_name']
    raw_id_fields = ['autism_diagnosis', 'specifier', 'stated_by', 'proposed_by', 'approved_by']


# ╔════════════════════════════════════════════╗ 
# ║         6. DIAGNOSIS DOCUMENT ✨          ║ 
# ╚════════════════════════════════════════════╝ 

@admin.register(DiagnosisDocument)
class DiagnosisDocumentAdmin(admin.ModelAdmin):
    list_display = ['client', 'file_name', 'document_type', 'is_approved', 'upload_date']
    list_filter = ['document_type', 'is_approved']
    search_fields = ['client__first_name', 'client__last_name', 'file_name']
    raw_id_fields = ['client', 'uploaded_by', 'approved_by']

# ╔════════════════════════════════════════════╗ 
# ║      7. DOCTOR SPECIALTY ADMINS 🤠       ║ 
# ╚════════════════════════════════════════════╝ 
#
@admin.register(MasterSpecialtyCategory)
class MasterSpecialtyCategory(admin.ModelAdmin):
    list_display = ['category_name', 'category_code', 'display_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['category_name', 'category_code']

@admin.register(MasterSpecialty)
class MasterSpecialtyAdmin(admin.ModelAdmin):
    list_display = ['specialty_name', 'category', 'specialty_code', 'is_active']
    list_filter = ['is_active', 'category']
    search_fields = ['specialty_name', 'specialty_code']
    raw_id_fields = ['category']
    # raw id fields for what actually ?? 
    #
# = adding the specialty to doctor =
@admin.register(DoctorSpecialty)
class DoctorSpecialty(admin.ModelAdmin):
    list_display = ['doctor', 'specialty', 'is_board_certified', 'is_primary_specialty']
    list_filter = ['is_board_certified', 'is_primary_specialty']
    search_fields = ['doctor__first_name', 'doctor__last_name', 'specialty__specialty_name']
    raw_id_fields = ['doctor', 'specialty']

# ╔════════════════════════════════════════════╗ 
# ║        8. CONVERSATION SECTON 💬         ║ 
# ╚════════════════════════════════════════════╝ 
# 
@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = [
        'client',
        'therapist',
        'sender_display',
        'is_from_client_display',
        'date',
        'time',
        'username',
        'message_preview',
        'cleaned_text_preview',
        'cleaned_text_topic',
        'chat_type',
        'sentiment_with_emoji',
        'sentiment_score_display',
        'uploaded_by',
        'upload_batch',
    ]

    list_filter = [
        'chat_type',
        'sentiment',
        'date',
        'uploaded_by',
        'is_from_client',
        'upload_batch',
    ]

    search_fields = [
        'client__first_name',
        'client__last_name',
        'therapist__first_name',
        'therapist__last_name',
        'sender__first_name',
        'sender__last_name',
        'username',
        'message',
        'cleaned_text',
    ]

    raw_id_fields = ['client', 'therapist','sender', 'uploaded_by', 'upload_history']

    readonly_fields = [
        'message_hash',
        'created_at',
        'updated_at',
        'uploaded_at',
    ]

    fieldsets = (
        ('Client Information', {
            'fields': ('client', 'username', 'chat_type')
        }),
        ('Message', {
            'fields': ('date', 'time', 'message', 'cleaned_text')
        }),
        ('Sentiment Analysis', {
            'fields': ('sentiment', 'sentiment_score', 'sentiment_confidence'),
            'classes': ('collapse',)
        }),
        ('Upload Information', {
            'fields': ('uploaded_by', 'upload_history', 'upload_batch', 'uploaded_at')
        }),
        ('System fields', {
            'fields': ('message_hash', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def sender_display(self, obj):
        """display sender name"""
        if obj.sender:
            return f"{obj.sender.get_full_name() or obj.sender.username}"

        return obj.username or "Uknown"
    sender_display.short_description = 'Sender'

    def is_from_client_display(self, obj):
        """display if message is from client with emoji"""
        if obj.is_from_client is None:
            return 'Uknown'
        if obj.is_from_client:
            return 'Client'
        else:
            return 'Therapist'
    is_from_client_display.short_description = 'From'

    def message_preview(self, obj):
        """Show truncated message preview. """
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Message'

    def cleaned_text_preview(self, obj):
        """show cleanded text."""
        if obj.cleaned_text:
            return obj.cleaned_text[:60] + '...' if len(obj.cleaned_text) > 60 else obj.cleaned_text
        return 'Not Cleaned'
    cleaned_text_preview.short_description = 'Cleaned'

    def sentiment_with_emoji(self, obj):
        """show sentiment with emoji for visual clarity"""
        if obj.sentiment == 'positive':
            return '😀 Positive'
        elif obj.sentiment == 'negative':
            return '😈 Negative'
        elif obj.sentiment == 'neutral':
            return '😮 Neutral'
        else:
            return 'None'
    sentiment_with_emoji.short_description = 'Sentiment'

    def sentiment_score_display(self, obj):
        """Display the sentiment score with color coding."""
        if obj.sentiment_score is None:
            return 'N/A'
        
        score = obj.sentiment_score
        if score > 0.3:
            color = 'green'
            emoji = '🟢'
        elif score < -0.3:
            color = 'red'
            emoji = '🔴'
        else:
            color = 'orange'
            emoji = '🟡'
        
        from django.utils.html import format_html
        return mark_safe(
            f'<span style="color: {color}; font-weight: bold;">{emoji} {score:.2f}</span>'
        )
    sentiment_score_display.short_description = 'Score'
# ╔════════════════════════════════════════════╗ 
# ║        9. UNMATCHED MESSAGE ADMIN          ║ 
# ╚════════════════════════════════════════════╝ 
#
@admin.register(UnmatchedMessage)
class UnmatchedMessageAdmin(admin.ModelAdmin):
    list_display = ['date', 'time', 'username', 'upload_batch']
    list_filter = ['date', 'upload_batch']
    search_fields = ['username', 'message']
    date_hierarchy = 'date'


# ╔════════════════════════════════════════════╗ 
# ║         10. UPLOAD HISTORY ADMIN           ║ 
# ╚════════════════════════════════════════════╝ 
# 
@admin.register(UploadHistory)
class UploadHistoryAdmin(admin.ModelAdmin):
    list_display = [
        'file_name',
        'uploaded_by',
        'uploaded_at',
        'message_count',
        'status',
        'positive_count',
        'negative_count',
        'neutral_count'
    ]
    list_filter = ['status', 'uploaded_at']
    search_fields = ['file_name', 'batch_id', 'uploaded_by__username']
    date_hierarchy = 'uploaded_at'
    raw_id_fields = ['uploaded_by']


# ╔════════════════════════════════════════════╗ 
# ║     11. TOPIC MODELING SECTIONS ADMIN      ║ 
# ╚════════════════════════════════════════════╝ 
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name', 'description']

@admin.register(ClientTopicScore)
class ClientTopicScoreAdmin(admin.ModelAdmin):
    list_display = ['client', 'topic', 'score', 'last_updated']
    list_filter = ['topic']
    search_fields = ['client__first_name', 'client__last_name', 'topic__name']
    raw_id_fields = ['client', 'topic']

@admin.register(MessageTopic)
class MessageTopicAdmin(admin.ModelAdmin):
    list_display = ['conversation', 'topic', 'score', 'confidence', 'analyzed_at']
    list_filter = ['topic', 'analyzed_at']
    search_fields = ['conversation__client__first_name', 'topic__name']
    raw_id_fields = ['conversation', 'topic']


# ╔════════════════════════════════════════════╗ 
# ║ADMIN CONFIGURATION SITE OVERRIDE THE DEFAUL║ 
# ╚════════════════════════════════════════════╝ 
admin.site.site_header = 'Sentiri - Autism Therapy System 🏥'
admin.site.site_title = 'Sentiri Admin'
admin.site.index_title = 'Welcome to Sentiri Administration'


