from django.contrib import admin, messages
from unfold.admin import ModelAdmin
from unfold.views import UnfoldModelAdminViewMixin
from django.views.generic import View
from django.shortcuts import redirect
from django.http import Http404
from .forms import UploadChatForm, UploadDocumentForm, ClientSpecifierForm, DoctorSpecialtyForm
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth import get_user_model
from .forms import CustomUserCreationForm, CustomUserChangeForm, AutismDiagnosisForm, MasterSpecifierForm, MasterSpecialtyForm, MasterSpecialtyCategoryForm, ClientContactForm
import csv
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django import forms
from django.urls import path
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
class CustomUserAdmin(UserAdmin, ModelAdmin):
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

    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom = [
            path(
                'client-cards/',
                self.admin_site.admin_view(ClientCardView.as_view()),
                name='chat_analyzer_client_cards',
            ),
        ]
        return custom + urls
# ╔════════════════════════════════════════════╗ 
# ║             2. CLIENT CONTACT              ║ 
# ╚════════════════════════════════════════════╝ 

@admin.register(ClientContact)
class ClientContactAdmin(admin.ModelAdmin):
    change_list_template = 'chat_analyzer/admin/client_contact/change_list.html'
    list_display = ['name', 'client', 'contact_type', 'phone_number', 'is_primary']
    list_filter = ['contact_type', 'is_primary']
    search_fields = ['name', 'phone_number', 'client__first_name', 'client__last_name']
    raw_id_fields = ['client']

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'upload_client_contact/',
                self.admin_site.admin_view(ClientContactView.as_view()),
                name='chat_analyzer_clientcontact_upload'
            )
        ]
        return custom + urls
# ╔════════════════════════════════════════════╗ 
# ║         ClientContactForm [Admin]          ║ 
# ╚════════════════════════════════════════════╝ 
class ClientContactView(UnfoldModelAdminViewMixin, View):
    
    title = "Creating new client contact"
    permission_required = "chat_analyzer.view_clientcontact"
    
    def get(self, request, *args, **kwargs):
        form = ClientContactForm()
        return self.render_template(request, 'chat_analyzer/admin/client_contact/upload_client_contact.html', {
            'form': form,
            'title': self.title,
        })
    
    def post(self, request, *args, **kwargs):
        form = ClientContactForm(self.POST)
        if form.is_valid():
            
            clientcontact = ClientContact.objects.create(
                client = form.cleaned_data['client'],
                contact_type = form.cleaned_data['contact_type'],
                name = form.cleaned_data['name'],
                phone_number = form.cleaned_data['phone_number'],
                is_primary = form.cleaned_data['is_primary'],
                notes = form.cleaned_data['notes'],
            )

            messages.success(
                request,
                f" successfully created contact for this {clientcontact.client} "
            )
            return redirect('admin:chat_analyzer_clientcontact_changelist')
        # if form is not valid
        return self.render_template(request, 'chat_analyzer/admin/client_contact/upload_client_contact.html', {
            'form': form,
            'title': self.title,
        })

    def render_template(self, request, template_name, context):
        """handling method"""
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from django.contrib import admin

        admin_site=admin.site
        admin_context=admin_site.each_context(request)
        context.update(admin_context)

        context.update({
            'opts': ClientContact._meta,
            'app_label': ClientContact._meta.app_label,
            'has_change_permission': True,
            'has_view_permission': True,
            'has_add_permission': True,
            'has_permission': True,
            'is_popup': False,
        })
        return HttpResponse(render_to_string(template_name, context, request))


# ╔════════════════════════════════════════════╗ 
# ║            3. AUTISM DIAGNOSIS             ║ 
# ╚════════════════════════════════════════════╝ 

@admin.register(AutismDiagnosis)
class AutismDiagnosisAdmin(admin.ModelAdmin):
    change_list_template = 'chat_analyzer/admin/autism_diagnosis/change_list.html',
    list_display = ['client', 'support_level', 'diagnosis_date', 'diagnosed_by', 'is_active']
    list_filter = ['support_level', 'is_active', 'diagnosis_date']
    search_fields = ['client__first_name', 'client__last_name', 'diagnosed_by__username']
    raw_id_fields = ['client', 'diagnosed_by']
    data_hierarchy = 'diagnosis_date'
    autocomplete_fields = ['client', 'diagnosed_by']

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'upload_diagnosis/',
                self.admin_site.admin_view(UploadAutismDiagnosisView.as_view()),
                name='chat_analyzer_autismdiagnosis_upload',
            )
        ]
        return custom + urls

# ╔════════════════════════════════════════════╗ 
# ║       AutismDiagnosisUpload [admin]        ║ 
# ╚════════════════════════════════════════════╝ 
class UploadAutismDiagnosisView(UnfoldModelAdminViewMixin, View):
    """custom views: upload diagnostic autism"""

    title = "Upload the diagnosis details"
    permission_required = "chat_analyzer.view_austismdiagnosis"

    def get(self, request, *args, **kwargs):
        form = AutismDiagnosisForm()
        return self.render_template(request, 'chat_analyzer/admin/autism_diagnosis/upload_diagnosis.html', {
            'form': form,
            'title': self.title,
        })

    def post(self, request, *args, **kwargs):
        form = AutismDiagnosisForm(request.POST)
        if form.is_valid():
            
            diagnosis = AutismDiagnosis.objects.create(
                client=form.cleaned_data['client'],
                support_level = form.cleaned_data['support_level'],
                diagnosed_by = form.cleaned_data['diagnosed_by'],
                diagnosis_date = form.cleaned_data['diagnosis_date'],
                clinical_notes = form.cleaned_data['clinical_notes'],
                is_active = form.cleaned_data['is_active'],
            )
            messages.success(
                request,
                f" Uploaded autism diagnosis for {diagnosis.client.get_full_name()}"
            )
            return redirect('admin:chat_analyzer_autismdiagnosis_changelist')

        # if forms has error we rendor with error messages
        return self.render_template(request, 'chat_analyzer/admin/autism_diagnosis/upload_diagnosis.html',{
            'form': form,
            'title': self.title,
        })

    def render_template(self, request, template_name, context):
        """helper method to render template"""
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from django.contrib import admin

        admin_site = admin.site
        admin_context = admin_site.each_context(request)
        context.update(admin_context)

        context.update({
            'opts': DiagnosisDocument._meta,
            'app_label': DiagnosisDocument._meta.app_label,
            'has_change_permission': True,
            'has_view_permission': True,
            'has_add_permission': True,
            'has_permission': True,
            'is_popup': False,
        })
        return HttpResponse(render_to_string(template_name, context, request))

# ╔════════════════════════════════════════════╗ 
# ║    4.  MASTER SPECIFIER : SLEEP ISSUES     ║ 
# ╚════════════════════════════════════════════╝ 

@admin.register(MasterSpecifier)
class MasterSpecifierAdmin(admin.ModelAdmin):
    change_list_template = 'chat_analyzer/admin/master_specifier/change_list.html'
    list_display = ['specifier_name', 'specifier_category', 'is_positive_specifier', 'is_active']
    list_filter = ['specifier_category', 'is_positive_specifier', 'is_active']
    search_fields = ['specifier_name', 'dsm_code']
    ordering = ['specifier_category', 'specifier_name']

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'upload_specifier/',
                self.admin_site.admin_view(MasterSpecifierView.as_view()),
                name='chat_analyzer_masterspecifier_upload',
            )
        ]
        return custom + urls
# ╔════════════════════════════════════════════╗ 
# ║         4.1 [MasterSpecifierForm]          ║ 
# ╚════════════════════════════════════════════╝ 
class MasterSpecifierView(UnfoldModelAdminViewMixin, View):
    title = "Master Specifier"
    permission_required = "chat_analyzer.view_masterspecifier"

    def get(self, request, *args, **kwargs):
        form = MasterSpecifierForm()
        return self.render_template(request, 'chat_analyzer/admin/master_specifier/upload_specifier.html', {
            'form': form,
            'title': self.title,
        })

    def post(self, request, *args, **kwargs):
        form = MasterSpecifierForm(request.POST)
        if form.is_valid():
            specifier = MasterSpecifier.objects.create(
                specifier_name = form.cleaned_data['specifier_name'],
                specifier_category = form.cleaned_data['specifier_category'],
                is_positive_specifier = form.cleaned_data['is_positive_specifier'],
                dsm_code = form.cleaned_data['dsm_code'],
                is_active = form.cleaned_data['is_active'],
                definition = form.cleaned_data['definition'],
            )
            messages.success(
                request,
                f" Successfully created {specifier.specifier_name} !"
            )
            return redirect('admin:chat_analyzer_masterspecifier_changelist')

        # if form is not valid or error
        return self.render_template(request, 'chat_analyzer/admin/master_specifier/upload_specifier.html',{
            'form': form,
            'title': self.title,
        })

    def render_template(self, request, template_name, context):
        """helper method to render the template"""
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from django.contrib import admin

        admin_site = admin.site
        admin_context = admin_site.each_context(request)
        context.update(admin_context)

        context.update({
            'opts': MasterSpecifier._meta,
            'app_label': MasterSpecifier._meta.app_label,
            'has_change_permission': True,
            'has_add_permission': True,
            'has_view_permission': True,
            'has_permission': True,
            'is_popup': False,
        })
        return HttpResponse(render_to_string(template_name, context, request))

# ╔════════════════════════════════════════════╗ 
# ║    5. CLIENT DETAIL SPECIFIER ASSOCIATE    ║ 
# ╚════════════════════════════════════════════╝ 
#
@admin.register(ClientSpecifier)
class ClientSpecifierAdmin(admin.ModelAdmin):
    change_list_template = "chat_analyzer/admin/client_specifier/change_list.html"
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

    def get_urls(self):
        """custom urls path"""
        urls = super().get_urls()
        custom = [
            path(
                'upload_client_specifier/',
                self.admin_site.admin_view(ClientSpecifierView.as_view()),
                name='chat_analyzer_clientspecifier_upload',
            )
        ]
        return custom + urls
# ╔════════════════════════════════════════════╗ 
# ║        ClientSpecifierView [admin]         ║ 
# ╚════════════════════════════════════════════╝ 
class ClientSpecifierView(UnfoldModelAdminViewMixin, View):
    
    title = "Detail Of Client Specifier"
    permission_required = "chat_analyzer.view_clientspecifier"

    def get(self, request, *args, **kwargs):
        form = ClientSpecifierForm()
        return self.render_template(request, 'chat_analyzer/admin/client_specifier/upload_client_specifier.html', {
            'form': form,
            'title': self.title,
        })

    def post(self, request, *args, **kwargs):
        form = ClientSpecifierForm(request.POST)
        if form.is_valid():
            clientspecifier = ClientSpecifier.objects.create(
                autism_diagnosis=form.cleaned_data['autism_diagnosis'],
                specifier=form.cleaned_data['specifier'],
                severity=form.cleaned_data['severity'],
                is_present=form.cleaned_data['is_present'],
                clinical_notes=form.cleaned_data['clinical_notes'],
                stated_by=form.cleaned_data['stated_by'],
                stated_date=form.cleaned_data['stated_date'],
                is_approved=form.cleaned_data['is_approved'],
            )

            messages.success(
                request,
                f" successfully created specifier for {clientspecifier.autism_diagnosis} !"
            )
            return redirect('admin:chat_analyzer_clientspecifier_changelist')
        # then if form is invalid
        return self.render_template(request, 'chat_analyzer/admin/client_specifier/upload_client_specifier.html', {
            'form': form,
            'title': self.title,
        })

    def render_template(self, request, template_name, context):
        """helper method"""
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from django.contrib import admin

        admin_site=admin.site
        admin_context=admin_site.each_context(request)
        context.update(admin_context)

        context.update({
            'opts': ClientSpecifier._meta,
            'app_label': ClientSpecifier._meta.app_label,
            'has_change_permission': True,
            'has_add_permission': True,
            'has_permission': True,
            'is_popup': False,
        })
        return HttpResponse(render_to_string(template_name, context, request))

# ╔════════════════════════════════════════════╗ 
# ║         6. DIAGNOSIS DOCUMENT ✨          ║ 
# ╚════════════════════════════════════════════╝ 

@admin.register(DiagnosisDocument)
class DiagnosisDocumentAdmin(admin.ModelAdmin):
    change_list_template = 'chat_analyzer/admin/diagnosis_documents/change_list.html',
    list_display = ['client', 'file', 'document_type', 'is_approved', 'upload_date']
    list_filter = ['document_type', 'is_approved']
    search_fields = ['client__first_name', 'client__last_name', 'file']
    autocomplete_fields = ['client', 'uploaded_by', 'approved_by']

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'upload_document/',
                self.admin_site.admin_view(UploadDocumentView.as_view()),
                name='chat_analyzer_diagnosisdocument_upload',
            )
        ]
        return custom + urls


class UploadDocumentView(UnfoldModelAdminViewMixin, View):
    """custom view: admin uploads diagnosis documents"""
    title = "Upload Diagnosis Document"
    permission_required = "chat_analyzer.view_diagnosisdocument"

    def get(self, request, *args, **kwargs):
        form = UploadDocumentForm()
        return self.render_template(request, 'chat_analyzer/admin/diagnosis_documents/upload_document.html', {
            'form': form,
            'title': self.title,
        })

    def post(self, request, *args, **kwargs):
        form = UploadDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            # save the document
            doc = DiagnosisDocument.objects.create(
                client=form.cleaned_data['client'],
                file=form.cleaned_data['file'],
                document_type=form.cleaned_data['document_type'],
                uploaded_by=request.user,
            )
            messages.success(
                request,
                f" Uploaded '{doc.file.name}' for {doc.client.get_full_name()}",
            )
            return redirect('admin:chat_analyzer_diagnosisdocument_changelist')

        # if form has errors - re render with errors
        return self.render_template(request, 'chat_analyzer/admin/diagnosis_documents/upload_document.html',{
            'form': form,
            'title': self.title,
        })

    def render_template(self, request, template_name, context):
        """helper method to render template with unfolds full admin content"""
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from django.contrib import admin

        admin_site = admin.site
        admin_context = admin_site.each_context(request)
        context.update(admin_context)

        context.update({
            'opts': DiagnosisDocument._meta,
            'app_label': DiagnosisDocument._meta.app_label,
            'has_change_permission': True,
            'has_view_permission': True,
            'has_add_permission': True,
            'has_permission': True,
            'is_popup': False,
        })
        return HttpResponse(render_to_string(template_name, context, request))

# ╔════════════════════════════════════════════╗ 
# ║      7. DOCTOR SPECIALTY ADMINS 🤠       ║ 
# ╚════════════════════════════════════════════╝ 
#
@admin.register(MasterSpecialtyCategory)
class MasterSpecialtyCategoryAdmin(admin.ModelAdmin):
    change_list_template = 'chat_analyzer/admin/master_specialty_category/change_list.html'
    list_display = ['category_name', 'category_code', 'is_active']
    list_filter = ['is_active']
    search_fields = ['category_name', 'category_code']

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'upload_specialty_category/',
                self.admin_site.admin_view(MasterSpecialtyCategoryView.as_view()),
                name='chat_analyzer_masterspecialtycategory_upload',
            )
        ]
        return custom + urls
    
# ╔════════════════════════════════════════════╗ 
# ║        MasterSpecialtyCategoryView         ║ 
# ╚════════════════════════════════════════════╝ 
class MasterSpecialtyCategoryView(UnfoldModelAdminViewMixin, View):
    
    title = "Add New Doctor Specialty Category"
    permission_required = "chat_analyzer.view_masterspecialtycategory"

    def get(self, request, *args, **kwargs):
        form = MasterSpecialtyCategoryForm()
        return self.render_template(request, 'chat_analyzer/admin/master_specialty_category/upload_specialty_category.html',{
            'form': form,
            'title': self.title,
        })

    def post(self, request, *args, **kwargs):
        form = MasterSpecialtyCategoryForm(request.POST)
        if form.is_valid():
            
            specialtycategory = MasterSpecialtyCategory.objects.create(
                category_name = form.cleaned_data['category_name'],
                category_code = form.cleaned_data['category_code'],
                category_description = form.cleaned_data['category_description'],
                is_active = form.cleaned_data['is_active'],
            )
            messages.success(
                request,
                f"You have successfully create {specialtycategory.category_name} !"
            )
            return redirect('admin:chat_analyzer_masterspecialtycategory_changelist')
        # if not valid
        return self.render_template(request, 'chat_analyzer/admin/master_specialty_category/upload_specialty_category.html',{
            'form': form,
            'title': self.title,
        })

    def render_template(self, request, template_name, context):
        """helper method to render template"""
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from django.contrib import admin

        admin_site=admin.site
        admin_context=admin_site.each_context(request)
        context.update(admin_context)

        context.update({
            'opts': MasterSpecialtyCategory._meta,
            'app_label': MasterSpecialtyCategory._meta.app_label,
            'has_change_permission': True,
            'has_view_permission': True,
            'has_add_permission': True,
            'has_permission': True,
            'is_popup': False,
        })
        return HttpResponse(render_to_string(template_name, context, request))

        







@admin.register(MasterSpecialty)
class MasterSpecialtyAdmin(admin.ModelAdmin):
    change_list_template = 'chat_analyzer/admin/master_specialty/change_list.html'
    list_display = ['specialty_name', 'category', 'specialty_code', 'is_active']
    list_filter = ['is_active', 'category']
    search_fields = ['specialty_name', 'specialty_code']
    raw_id_fields = ['category']
    # raw id fields for what actually ?? 
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'upload_specialty/',
                self.admin_site.admin_view(MasterSpecialtyView.as_view()),
                name='chat_analyzer_masterspecialty_upload',
            )
        ]
        return custom + urls
# ╔════════════════════════════════════════════╗ 
# ║            MasterSpecialtyView             ║ 
# ╚════════════════════════════════════════════╝ 
class MasterSpecialtyView(UnfoldModelAdminViewMixin, View):
    title = "Doctor Specialty"
    permission_required = "chat_analyzer.view_masterspecialty"

    def get(self,request, *args, **kwargs):
        form = MasterSpecialtyForm()
        return self.render_template(request, 'chat_analyzer/admin/master_specialty/upload_specialty.html', {
            'form': form,
            'title': self.title,
        })

    def post(self, request, *args, **kwargs):
        form = MasterSpecialtyForm(request.POST)
        if form.is_valid():
            specialty = MasterSpecialty.objects.create(
                specialty_name = form.cleaned_data['specialty_name'],
                specialty_code = form.cleaned_data['specialty_code'],
                category = form.cleaned_data['category'],
                is_active = form.cleaned_data['is_active'],
            )
            messages.success(
                request,
                f" Successfully Created {specialty.specialty_name} !"
            )
        # invalid forms error
        return self.render_template(request, 'chat_analyzer/admin/master_specialty/upload_specialty.html', {
            'form': form,
            'title': self.title,
        })

    def render_template(self, request, template_name, context):
        """helper method to render template"""
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from django.contrib import admin

        admin_site = admin.site
        admin_context = admin_site.each_context(request)
        context.update(admin_context)

        context.update({
            'opts': MasterSpecialty._meta,
            'app_label': MasterSpecialty._meta.app_label,
            'has_change_permission': True,
            'has_view_permission': True,
            'has_add_permission': True,
            'has_permission': True,
            'is_popup': False,
        })
        return HttpResponse(render_to_string(template_name, context, request))


    
# = adding the specialty to doctor =
@admin.register(DoctorSpecialty)
class DoctorSpecialtyAdmin(admin.ModelAdmin):
    change_list_template = "chat_analyzer/admin/doctor_specialty/change_list.html"
    list_display = ['doctor', 'specialty', 'is_board_certified', 'is_primary_specialty']
    list_filter = ['is_board_certified', 'is_primary_specialty']
    search_fields = ['doctor__first_name', 'doctor__last_name', 'specialty__specialty_name']
    raw_id_fields = ['doctor', 'specialty']

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'upload_doctor_specialty/',
                self.admin_site.admin_view(DoctorSpecialtyView.as_view()),
                name="chat_analyzer_doctorspecialty_upload",
            )
        ]
        return custom + urls

# ╔════════════════════════════════════════════╗ 
# ║        DoctorSpecialtyView [admin]         ║ 
# ╚════════════════════════════════════════════╝ 
class DoctorSpecialtyView(UnfoldModelAdminViewMixin, View):
    title="Doctor Specialty Details"
    permission_required = "chat_analyzer.view_doctorspecialty"

    def get(self, request, *args, **kwargs):
        form = DoctorSpecialtyForm()
        return self.render_template(request, 'chat_analyzer/admin/doctor_specialty/upload_doctor_specialty.html',{
            'form': form,
            'title': self.title,
        })

    def post(self, request, *args, **kwargs):
        form = DoctorSpecialtyForm(request.POST)
        if form.is_valid():
            doctorspecialty=DoctorSpecialty.objects.create(
                doctor=form.cleaned_data['doctor'],
                specialty=form.cleaned_data['specialty'],
                is_board_certified=form.cleaned_data['is_board_certified'],
                certification_date=form.cleaned_data['certification_date'],
                certification_expires=form.cleaned_data['certification_expires'],
                is_primary_specialty=form.cleaned_data['is_primary_specialty'],
            )
            messages.success(
                request,
                f" You have successfully assign this {doctorspecialty.doctor} his specialty !"
            )
            return redirect('admin:chat_analyzer_doctorspecialty_changelist')

        # if not valid
        return render_template(request, 'chat_analzyer/admin/doctor_specialty/upload_doctor_specialty.html', {
            'form': form,
            'title': self.title,
        })

    def render_template(self, request, template_name, context):
        
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from django.contrib import admin

        admin_site=admin.site
        admin_context=admin_site.each_context(request)
        context.update(admin_context)

        context.update({
            'opts': DoctorSpecialty._meta,
            'app_label': DoctorSpecialty._meta.app_label,
            'has_change_permission': True,
            'has_view_permission': True,
            'has_add_permission': True,
            'has_permission': True,
            'is_popup': False,
        })
        return HttpResponse(render_to_string(template_name, context, request))

# ╔════════════════════════════════════════════╗ 
# ║        8. CONVERSATION SECTON 💬         ║ 
# ╚════════════════════════════════════════════╝ 
# ── Unfold-styled Upload View ─────────────────────────────
class UploadChatsView(UnfoldModelAdminViewMixin, View):
    from chat_analyzer.services.upload_service import process_whatsapp_upload
    """Custom view: therapist/admin uploads WhatsApp .txt from admin panel.
    Uses UnfoldModelAdminViewMixin so Unfold's CSS/JS/theme is injected."""
    title = "Upload WhatsApp Chat"
    permission_required = "chat_analyzer.view_conversation"

    def get(self, request, *args, **kwargs):
        form = UploadChatForm()
        return self.render_template(request, 'chat_analyzer/admin/conversations/upload_chats.html', {
            'form': form,
            'title': self.title,
        })

    def post(self, request, *args, **kwargs):
        form = UploadChatForm(request.POST, request.FILES)
        if form.is_valid():
            result = process_whatsapp_upload(
                file_path_or_file=request.FILES['chat_file'],
                client_id=form.cleaned_data['client'].id,
                uploader_id=request.user.id,
                chat_type=form.cleaned_data['chat_type'],
                therapist_id=form.cleaned_data.get('therapist').id if form.cleaned_data.get('therapist') else None,
            )
            if 'error' in result:
                from django.contrib import messages
                messages.error(request, f"❌ {result['error']}")
            else:
                # auto-retrain topics
                from chat_analyzer.services.topic_modeler import train_topics
                try:
                    train_topics()
                except Exception as e:
                    from django.contrib import messages
                    messages.warning(request, f"⚠️ Topic training failed: {e}")

                from django.contrib import messages
                messages.success(
                    request,
                    f"✅ Saved {result['saved']} messages as '{result.get('file_name', '')}' "
                    f"({result['positive']} pos / {result['negative']} neg / {result['neutral']} neu) — "
                    f"topics retrained",
                )
            return redirect('admin:chat_analyzer_conversation_changelist')
        # Form has errors — re-render with errors
        return self.render_template(request, 'chat_analyzer/admin/conversations/upload_chats.html', {
            'form': form,
            'title': self.title,
        })

    def render_template(self, request, template_name, context):
        """Helper to render template with Unfold's full admin context."""
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from django.contrib import admin

        # Pull in Unfold's admin context (colors, theme, border_radius, etc.)
        admin_site = admin.site
        admin_context = admin_site.each_context(request)
        context.update(admin_context)

        form = context.get('form')
        context.update({
            'opts': Conversation._meta,
            'app_label': Conversation._meta.app_label,
            'has_change_permission': True,
            'has_view_permission': True,
            'has_add_permission': True,
            'has_permission': True,
            'is_popup': False,
            'to_field': None,
            'title': context.get('title', ''),
            'cl': None,
            'save_as': False,
            'save_on_top': False,
            'add': False,
            'change': False,
            'preserve_filters': False,
            'actions_on_top': False,
            'actions_on_bottom': False,
            'media': form.media if form else None,
        })

        return HttpResponse(render_to_string(template_name, context, request=request))


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    change_list_template = 'chat_analyzer/admin/conversations/change_list.html'
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
        'topic_tags_display',
        'chat_type',
        'sentiment_with_emoji',
        'sentiment_score_display',
        'sentiment_confidence',
        'is_processed',
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
        'topics__topic',
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

    actions = ['mark_as_processed']

    @admin.action(description="Mark selected conversations as processed")
    def mark_as_processed(self, request, queryset):
        count = queryset.update(is_processed=True)
        self.message_user(request, f"✅ Marked {count} conversation(s) as processed")

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

    def topic_tags_display(self, obj):
        """Show topic tags assigned to this conversation."""
        from django.utils.html import format_html, format_html_join

        links = obj.topics.all()
        if not links:
            return format_html('<span style="color: gray;">{}</span>', '— no topic —')

        def badge_parts(mt):
            conf = mt.confidence or 0
            if conf >= 0.7:
                color, dot = '#2e7d32', '🟢'
            elif conf >= 0.4:
                color, dot = '#ef6c00', '🟡'
            else:
                color, dot = '#c62828', '🔴'
            return (color, dot, mt.topic.name, f'{conf:.2f}')

        return format_html_join(
            ' ',
            '<span style="background: {}; color: white; padding: 2px 6px;'
            ' border-radius: 3px; margin: 1px; font-size: 11px;">{} {} ({})</span>',
            (badge_parts(mt) for mt in links),
        )
    topic_tags_display.short_description = 'Topics'

    def get_urls(self):
        """Add custom upload URL to admin."""
        urls = super().get_urls()
        custom = [
            path(
                'upload-chats/',
                self.admin_site.admin_view(UploadChatsView.as_view()),
                name='chat_analyzer_conversation_upload',
            ),
        ]
        return custom + urls


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
    list_display = ['name', 'status', 'is_active', 'created_at']
    list_filter = ['status', 'is_active']
    search_fields = ['name', 'description']

    actions = ['promote_to_active', 'archive_topics']

    @admin.action(description="Promote selected discovered topics to ACTIVE")
    def promote_to_active(self, request, queryset):
        # Only promote topics currently in 'discovered' state
        candidates = queryset.filter(status='discovered')
        count = candidates.update(status='active', is_active=True)
        self.message_user(request, f"✅ Promoted {count} topic(s) to ACTIVE")

    @admin.action(description="Archive selected topics (retired, kept for history)")
    def archive_topics(self, request, queryset):
        count = queryset.update(status='archived', is_active=False)
        self.message_user(request, f"📦 Archived {count} topic(s)")

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
# ║           CLIENTCARDVIEWSETUP []           ║ 
# ╚════════════════════════════════════════════╝ 
class ClientCardView(UnfoldModelAdminViewMixin, View):
    """card-style client overview with line charts."""
    title = "Client Cards"
    permission_required = "chat_analyzer.view_user"

    def get(self, request, *args, **kwargs):
        from django.db.models import Count, Sum, Q
        import json

        clients = User.objects.filter(role='client', is_active=True)

        cards = []
        for client in clients:
            # diagnosis first
            diagnosis = AutismDiagnosis.objects.filter(
                 client=client, is_active=True
            ).first()

            # Document + specifiers count
            doc_count = DiagnosisDocument.objects.filter(client=client).count()
            specifier_count = ClientSpecifier.objects.filter(
                autism_diagnosis__client=client
            ).count()

            specifiers = ClientSpecifier.objects.filter(
                autism_diagnosis__client=client,
                autism_diagnosis__is_active=True,
            ).select_related('specifier')[:5]

            # then after we get the queryset we need to create the list of the specifier for this client
            specifier_data = [
                {
                    "name": cs.specifier.specifier_name,
                    "severity": cs.severity,
                    "present": cs.is_present,
                    "definition": cs.specifier.definition,
                }
                for cs in specifiers
            ]
            # topic breakdown (from ClientTopicScore)
            topic_scores = ClientTopicScore.objects.filter(
                client=client, topic__status='active'
            ).select_related('topic').order_by('-score')[:5]

            topics_data = [
                {"name": ts.topic.name, "count": ts.message_count, "score": ts.score}
                for ts in topic_scores
            ]

            # sentiment totals
            convs = Conversation.objects.filter(client=client, sentiment__isnull=False)
            sentiment_totals = convs.aggregate(
                positive=Count('id', filter=Q(sentiment='positive')),
                negative=Count('id', filter=Q(sentiment='negative')),
                neutral=Count('id', filter=Q(sentiment='neutral')),
            )

            # line chart data 5 topic lines over time
            progress = (
                Conversation.objects
                .filter(client=client, sentiment__isnull=False, date__isnull=False)
                .values('date', 'topics__topic__name')
                .annotate(
                    score=Sum('sentiment_score'),
                    positive=Count('id', filter=Q(sentiment='positive')),
                    negative=Count('id', filter=Q(sentiment='negative')),
                    neutral=Count('id', filter=Q(sentiment='neutral')),
                )
                .order_by('date')
            )

            date_strings = [p['date'].strftime('%Y-%m-%d') for p in progress]
            scores = [p['score'] for p in progress]

            chart_data = json.dumps({
                "labels": date_strings,
                "datasets": [{
                    "label": "Sentiment Progress",
                    "data": scores,
                    "borderColor": "#10b981",
                    "backgroundColor": "rgba(16, 185, 129, 0.1)",
                    "fill": True,
                    "tension": 0.3,
                }],
            })

            cards.append({
                'client': client,
                'diagnosis': diagnosis,
                'doc_count': doc_count,
                'specifier_count': specifier_count,
                'specifier_data': specifier_data,
                'topics_data': topics_data,
                'sentiment': sentiment_totals,
                'chart_data': chart_data,
            })

        return self.render_template(
            request,
            'chat_analyzer/admin/client_cards/client_card.html',
            {'cards': cards, 'title': self.title}
        )

    def render_template(self, request, template_name, context):
        from django.template.loader import render_to_string
        from django.http import HttpResponse
        from django.contrib import admin

        admin_site = admin.site
        admin_context = admin_site.each_context(request)
        context.update(admin_context)

        from chat_analyzer.models import User
        context.update({
            'opts': User._meta,
            'app_label': User._meta.app_label,
            'has_change_permission': True,
            'has_view_permission': True,
            'has_add_permission': True,
            'is_popup': False,
        })
        return HttpResponse(render_to_string(template_name, context, request))

# ╔════════════════════════════════════════════╗ 
# ║ADMIN CONFIGURATION SITE OVERRIDE THE DEFAUL║ 
# ╚════════════════════════════════════════════╝ 
admin.site.site_header = 'Sentiri - Autism Therapy System 🏥'
admin.site.site_title = 'Sentiri Admin'
admin.site.index_title = 'Welcome to Sentiri Administration'


