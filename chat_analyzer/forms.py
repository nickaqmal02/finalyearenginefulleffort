from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, UserChangeForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Div, HTML, Fieldset
from django.conf import settings
from django.forms import inlineformset_factory
from .utils import normalize_phone_number

User = get_user_model()
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
