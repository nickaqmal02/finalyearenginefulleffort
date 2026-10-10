from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from django.conf import settings
from django.forms import inlineformset_factory
from .utils import normalize_phone_number
from .models import Conversation, DiagnosisDocument, AutismDiagnosis, MasterSpecifier, MasterSpecialtyCategory, MasterSpecialtyCategory, ClientContact, ClientSpecifier, DoctorSpecialty, MasterSpecialty
from unfold.widgets import UnfoldAdminSelectWidget, UnfoldAdminTextInputWidget, UnfoldAdminFileFieldWidget
from unfold.layout import Submit, Button
from crispy_forms.layout import Layout, Fieldset, HTML

User = get_user_model()

class UploadChatForm(forms.Form):

    """form for uploading whatsapp .txt files from admin panel"""
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(role='client', is_active=True),
        widget=UnfoldAdminSelectWidget,
        help_text="select the client this chat is about",
    )
    chat_file = forms.FileField(
        label='WhatsApp .txt file',
        widget=UnfoldAdminFileFieldWidget,
    )
    chat_type = forms.ChoiceField(
        choices=Conversation.CHAT_TYPES,
        initial='individual',
        widget=UnfoldAdminSelectWidget,
        help_text="What type of chat is this ?",
    )
    therapist = forms.ModelChoiceField(
        queryset=User.objects.filter(role='therapist', is_active=True),
        widget=UnfoldAdminSelectWidget,
        help_text="only required when it is about one on one chat",
    )
    def clean(self):
        cleaned_data = super().clean()
        chat_type = cleaned_data.get('chat_type')
        therapist = cleaned_data.get('therapist')

        if chat_type == 'individual' and not therapist:
            raise forms.ValidationError(
                "1-on-1 chats require a therapist. Select which therapist this chat was with"
            )
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Upload Details',
                'client',
                'chat_file',
                'chat_type',
                'therapist',
            ),
            Submit('submit', 'Upload and Process', css_class='!mx-6 !my-6'),
            Button(
                'cancel',                          # name
                'Cancel',                          # label
                css_class='ml-2',                  # spacing
                onclick='window.location.href="/admin/chat_analyzer/conversation/";'
            )
        )

    

# creating our own custom user creation form
class CustomUserCreationForm(UserCreationForm):
    """Custom form for creating new users in admin"""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('therapist', 'Therapist'),
        ('doctor', 'Doctor'),
        ('client', 'Client'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]

    # add our custom fields here ...
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        label="Role"
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Phone"
    )
    date_of_birth = forms.DateField(
        required=False,
        label="Date of Birth",
        widget=forms.DateInput(attrs={'type':'date'})
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        label="Gender"
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Address"
    )
    license_number = forms.CharField(
        max_length=255,
        required=False,
        label="license Number"
    )
    license_state = forms.CharField(
        max_length=255,
        required=False,
        label="License State"
    )
    years_of_experience = forms.IntegerField(
        required=False,
        label="Years of Experience"
    )
    hire_date = forms.DateField(
        required=False,
        label="Hire Date",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    specialization = forms.CharField(
        max_length=200,
        required=False,
        label="Specialization"
    )
    client_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="Client Status"
    )
    registered_by = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Registered By"
    )
    assigned_therapist = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Assigned Therapist"
    )

    class Meta:
        model = User
        fields = [
            'username',
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
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ Populate querysets at runtime, not import time
        self.fields['registered_by'].queryset = User.objects.filter(role='admin')
        self.fields['assigned_therapist'].queryset = User.objects.filter(role='therapist')


class CustomUserChangeForm(UserChangeForm):
    """Custom form for editing users in admin."""
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('therapist', 'Therapist'),
        ('doctor', 'Doctor'),
        ('client', 'Client'),
    ]
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        required=True,
        label="Role"
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        label="Phone"
    )
    date_of_birth = forms.DateField(
        required=False,
        label="Date of Birth",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        required=False,
        label="Gender"
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        label="Address"
    )
    license_number = forms.CharField(
        max_length=255,
        required=False,
        label="License Number"
    )
    license_state = forms.CharField(
        max_length=255,
        required=False,
        label="License State"
    )
    years_of_experience = forms.IntegerField(
        required=False,
        label="Years of Experience"
    )
    hire_date = forms.DateField(
        required=False,
        label="Hire Date",
        widget=forms.DateInput(attrs={'type': 'date'})
    )
    specialization = forms.CharField(
        max_length=200,
        required=False,
        label="Specialization"
    )
    client_status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label="Client Status"
    )
    registered_by = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Registered By"
    )
    assigned_therapist = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label="Assigned Therapist"
    )

    class Meta:
        model = User
        fields = [
            'username',
            'password',
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
        ]
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ✅ Populate querysets at runtime, not import time
        self.fields['registered_by'].queryset = User.objects.filter(role='admin')
        self.fields['assigned_therapist'].queryset = User.objects.filter(role='therapist')

# ╔════════════════════════════════════════════╗ 
# ║AUTHENTICATION FORMS 'LOGIN', 'LOGOUT', SIGN║ 
# ╚════════════════════════════════════════════╝ 
class CustomLoginForm(AuthenticationForm):
    """
    We use custom login form with crispy forms layout
    """
    def init(self, *args, **kwargs):
        super().init(args, **kwargs)

        # add placeholder to the fields
        self.fields['username'].widget.attrs.update({
            'class': 'w-full bg-gray-50 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5',
            'placeholder': 'Enter your username'
        })

        self.fields['password'].widget.attrs.update({
            'class': 'w-full bg-gray-50 border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5',
            'placeholder': '••••••••'
        })


#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  Sign Up Section :)                        
#━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
class CustomSignUpForm(UserCreationForm):
    """Custom signup form with Tailwind styling - No Crispy"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'w-full bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 pl-10',
            'placeholder': 'Enter your email'
        })
    )
    
    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'w-full bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 pl-10'
        })
    )
    
    first_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 pl-10',
            'placeholder': 'Enter your first name'
        })
    )
    
    last_name = forms.CharField(
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 pl-10',
            'placeholder': 'Enter your last name'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role', 'first_name', 'last_name')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add Tailwind classes to default fields
        self.fields['username'].widget.attrs.update({
            'class': 'w-full bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 pl-10',
            'placeholder': 'Choose a username'
        })
        self.fields['password1'].widget.attrs.update({
            'class': 'w-full bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 pl-10',
            'placeholder': 'Create a password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'w-full bg-gray-50 border border-gray-300 text-gray-900 rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 pl-10',
            'placeholder': 'Confirm your password'
        })
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("This email is already registered.")
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

# ╔════════════════════════════════════════════╗ 
# ║           UploadDocument [admin]           ║ 
# ╚════════════════════════════════════════════╝ 
class UploadDocumentForm(forms.Form):
    """Form for uploading diagnosis documents from admin panel"""
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(
        role='client',
        is_active=True,
        ),
        widget=UnfoldAdminSelectWidget,
        help_text="Select the client this document belongs to",
    )
    file = forms.FileField(
        label='DiagnosisDocument',
        widget=UnfoldAdminFileFieldWidget,
        help_text="Allowed: PDF, DOCX, PNG, JPG",
    )
    document_type = forms.ChoiceField(
        choices=DiagnosisDocument.DOCUMENT_TYPES,
        initial='diagnostic_report',
        widget=UnfoldAdminSelectWidget,
        help_text="Type of document",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False,
        self.helper.layout = Layout(
            Fieldset(
                'Upload Details',
                'client',
                'file',
                'document_type',
            ),
            Submit('submit', 'Upload Document', css_class='!mx-6 mt-2 !rounded-full'),
            Button(
                'cancel',
                'Cancel',
                css_class='ml-2 !rounded-full',
                onclick='window.location.href="/admin/chat_analyzer/diagnosisdocument/";'
            )
        )

# ╔════════════════════════════════════════════╗ 
# ║          UploadDIagnosis [admin]           ║ 
# ╚════════════════════════════════════════════╝ 
class AutismDiagnosisForm(forms.Form):
    """ custom form for uploading the AutismDiagnosisForm """
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(
            role='client',
            is_active=True,
        ),
        widget=UnfoldAdminSelectWidget,
        help_text="Select the client this diagnosis belongs to",
    )

    support_level = forms.ChoiceField(
        choices=AutismDiagnosis.SUPPORT_LEVEL_CHOICES,
        widget=UnfoldAdminSelectWidget,
        help_text="level of support for this client",
    )

    diagnosed_by = forms.ModelChoiceField(
        queryset = User.objects.filter(
            role='doctor',
            is_active=True,
        ),
        widget=UnfoldAdminSelectWidget,
        help_text="who diagnosed this ?",
    )
    diagnosis_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    clinical_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        required=False,
    )

    is_active = forms.BooleanField(
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Diagnosis Details',
                'client',
                'diagnosed_by',
                'support_level',
                'diagnosis_date',
                'is_active',
                'clinical_notes',
            ),
            Submit('submit', 'Upload Diagnosis', css_class='!mx-6 mt-2 !rounded-full'),
            Button(
                'cancel',
                'Cancel',
                css_class='ml-2 !rounded-full',
                onclick='window.location.href="/admin/chat_analyzer/autismdiagnosis/";'
            )
        )
# ╔════════════════════════════════════════════╗ 
# ║        MasterSpecifierForms[admin]         ║ 
# ╚════════════════════════════════════════════╝ 
class MasterSpecifierForm(forms.Form):
    """custom form: master specifier"""
    specifier_name = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text="name of the specifier",
    )

    specifier_category = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text="category of specifier e.g. Language",
    )

    is_positive_specifier = forms.BooleanField(
        required=False,
    )

    dsm_code = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text="DSM-5 reference code ="
    )

    is_active = forms.BooleanField(
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'SPECIFIERS DETAILS',
                'specifier_name',
                'specifier_category',
                'is_positive_specifier',
                'dsm_code',
                'is_active',
            ),
            Submit('submit', 'Submit', css_class="!mx-6 !mt-2 !rounded-full"),
            Button(
                'cancel',
                'Cancel',
                css_class='ml-2 !rounded-full',
                onclick='window.location.href="/admin/chat_analyzer/masterspecifier"'
            )
        )


# ╔════════════════════════════════════════════╗ 
# ║     MasterSpecialtyForm [ Admin ]          ║ 
# ╚════════════════════════════════════════════╝ 
class MasterSpecialtyForm(forms.Form):
    
    specialty_name = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text="e.g. Tecnical",
    )

    specialty_code = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text=" e.g SP_01",
    )

    category = forms.ModelChoiceField(
        queryset=MasterSpecialtyCategory.objects.filter(is_active=True),
        widget=UnfoldAdminSelectWidget,
        help_text="select the category for this specialty",
    )

    is_active = forms.BooleanField(
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'AVAILABLE DOCTOR SPECIALTY',
                'specialty_name',
                'specialty_code',
                'category',
                'is_active',
            ),
            Submit('submit', 'Submit', css_class="!mx-6 !mt-2 !rounded-full"),
            Button(
                'cancel',
                'Cancel',
                css_class="!ml-2 !rounded-full",
                onclick='window.location.href="/admin/chat_analyzer/masterspecialty"'
            )
        )
    
# ╔════════════════════════════════════════════╗ 
# ║         SPECIALTYCATEGORY [ADMIN]          ║ 
# ╚════════════════════════════════════════════╝ 
class MasterSpecialtyCategoryForm(forms.Form):
    category_name = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text="e.g Verbal",
    )
    category_code = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text="e.g. CA_01",
    )
    category_description = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text="the doctor have professional cert in this fields",
    )
    is_active = forms.BooleanField(
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Doctor Specialty Category',
                'category_name',
                'category_code',
                'category_description',
                'is_active',
            ),
            Submit('submit', 'Submit', css_class="!mx-6 !mt-2 !rounded-full"),
            Button(
                'cancel',
                'Cancel',
                css_class="!ml-2 !rounded-full",
                onclick='window.location.href="/admin/chat_analyzer/masterspecialtycategory"',
            )
        )

# ╔════════════════════════════════════════════╗ 
# ║         CLIENTCONTACTFORM [ADMIN]          ║ 
# ╚════════════════════════════════════════════╝ 
class ClientContactForm(forms.Form):
    
    client = forms.ModelChoiceField(
        queryset=User.objects.filter(
            role='client',
            is_active=True,
        ),
        widget=UnfoldAdminSelectWidget,
        help_text="client for this phone numbers",
    )

    contact_type = forms.ChoiceField(
        choices=ClientContact.CONTACT_TYPES,
        widget=UnfoldAdminSelectWidget,
        help_text="e.g. Father ? ",
    )

    name = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text="name for this contact number",
    )

    phone_number = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text="Contact phone number",
    )

    is_primary = forms.BooleanField(
        required=False,
    )

    notes = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        help_text="Additional notes about this contact",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                'Client Contact',
                'client',
                'contact_type',
                'name',
                'phone_number',
                'is_primary',
                'notes',
            ),
            Submit('submit', 'Submit', css_class="!mx-6 !rounded-full"),
            Button(
                'cancel',
                'Cancel',
                css_class = "!mx-6 !rounded-full",
                onclick='window.location.href="/admin/chat_analyzer/clientcontact"',
            )
        )

# ╔════════════════════════════════════════════╗ 
# ║        ClientSpecifiersForm [admin]        ║ 
# ╚════════════════════════════════════════════╝ 
class ClientSpecifierForm(forms.Form):
    """ Form for linking a specifier to a client's autism diagnosis"""
    
    autism_diagnosis = forms.ModelChoiceField(
        queryset=AutismDiagnosis.objects.filter(
            is_active=True,
        ),
        widget=UnfoldAdminSelectWidget,
        help_text="select the client's autism diagnosis",
    )

    specifier = forms.ModelChoiceField(
        queryset=MasterSpecifier.objects.filter(
            is_active=True,
        ),
        widget=UnfoldAdminSelectWidget,
        help_text="Select the specifier from the master list",
    )

    severity = forms.ChoiceField(
        choices=ClientSpecifier.SEVERITY_CHOICES,
        widget=UnfoldAdminSelectWidget,
        required=False,
        help_text="Severity level (if applicable)",
    )

    is_present = forms.BooleanField(
        required=False,
        help_text="True = client has this specifier, False = Client does NOT have it",
    )

    clinical_notes = forms.CharField(
        widget=UnfoldAdminTextInputWidget,
        required=False,
        help_text="Clinical description of how this specifier presents",
    )

    stated_by = forms.ModelChoiceField(
        queryset = User.objects.filter(role='doctor', is_active=True),
        required=False,
        help_text="Doctor who stated this specifier on this client",
    )

    stated_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="When this specifier was stated",
    )

    is_approved = forms.BooleanField(
        required=False,
        help_text="check if already approved (default=False)",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.form_tag=False,
        self.helper.layout=Layout(
            Fieldset(
                'CLIENT AUTISM SPECIFIERS',
                'autism_diagnosis',
                'specifier',
                'severity',
                'is_present',
                'clinical_notes',
                'stated_by',
                'stated_date',
                'is_approved',
            ),
            Submit('submit', 'Submit', css_class="!mx-6 !rounded-full"),
            Button(
                'cancel',
                'Cancel',
                css_class="!rounded-full",
                onclick='window.location.href="/admin/chat_analyzer/clientspecifier"',
            )
        )

# ╔════════════════════════════════════════════╗ 
# ║        EachDoctorSpecialty [admin]         ║ 
# ╚════════════════════════════════════════════╝ 
class DoctorSpecialtyForm(forms.Form):

    doctor=forms.ModelChoiceField(
        queryset=User.objects.filter(
            role='doctor',
            is_active=True,
        ),
        widget=UnfoldAdminSelectWidget,
        help_text="doctor's who own this specialty",
    )

    specialty=forms.ModelChoiceField(
        queryset=MasterSpecialty.objects.filter(
            is_active=True,
        ),
        widget=UnfoldAdminSelectWidget,
        help_text="The specialty that this doctor's own"
    )

    is_board_certified=forms.BooleanField(
        required=False,
    )

    certification_date=forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="the date of doctor's certificate",
    )

    certification_expires=forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False,
        help_text="Date of the doctor's certificate expired",
    )

    is_primary_specialty=forms.BooleanField(
        required=False,
    )

    # so to connect and allowing parsing value between this forms and another files we need to define __init__ method
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper=FormHelper()
        self.form_tag=False
        self.helper.layout=Layout(
            Fieldset(
                'Doctor Specialty Assignment',
                'doctor',
                'specialty',
                'is_board_certified',
                'certification_date',
                'certification_expires',
                'is_primary_specialty',
            ),
            Submit('submit', 'Submit', css_class="!mx-6 !rounded-full"),
            Button(
                'cancel',
                'Cancel',
                css_class="!rounded-full",
                onclick='window.location.href="/admin/doctorspecialty"',
            ),
        )












