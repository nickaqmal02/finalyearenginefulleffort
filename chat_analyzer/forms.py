from django import forms
from django.conf import settings
from .models import Admin, Client, Therapist

class LoginForm(forms.Form):
    username = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        })
    )

class AdminRegisterationForm(forms.ModelForm):
    # Explicitly define password with PasswordInput because crispy forms will override it
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    confirm_password = forms.CharField(
        widget=forms.PasswordInput()
        )
    invite_code = forms.CharField(
        max_length=100,
        help_text = 'you need an invite code to register as admin'
    )

    class Meta:
        model = Admin
        fields = ['username', 'name', 'phone_number', 'password']
        widget = {
            
        }

    def clean_invite_code(self):
        code = self.cleaned_data.get('invite_code')
        if code != settings.ADMIN_INVITE_CODE:
            raise forms.ValidationError('Invalid invite code. Please contact system administrator')
        return code
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Admin.objects.filter(username=username).exists():
            raise forms.ValidationError('username already exixts')
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match')
        
        return cleaned_data
    
    def save(self, commit=True):
        admin = super().save(commit=False)
        admin.set_password(self.cleaned_data['password'])
        if commit:
            admin.save()
        return admin
    


# adding client forms
class ClientRegisterationForm(forms.ModelForm):

    class Meta:
        model = Client
        fields = ['username','parent_name','child_name','phone_number','address','status','assigned_therapist']
        widgets = {
            'address': forms.Textarea(attrs={
                'rows': 3
            }),

        }
    
    def __init__(self, *args, **kwargs):
        admin_id = kwargs.pop('admin_id', None)
        super().__init__(*args, **kwargs)
        if admin_id:
            self.fields['assigned_therapist'].queryset = Therapist.objects.filter(registered_by_id=admin_id)
        
# client sections done

# ================== THERAPIST SECTION ================== #
class TherapistRegistrationForm(forms.ModelForm):

    class Meta:
        model = Therapist
        fields = ['username', 'password', 'name', 'phone_number', 'specialization', 'registered_by', 'is_active']
        widget = {
            'password': forms.PasswordInput(),
        }
    # here we wa
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Therapist.objects.filter(username=username).exists():
            raise forms.ValidationError('Username already exists')
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError('password do not match')
        
        return cleaned_data
    
    # segment for saving
    def save(self, commit=True, admin_id=None):
        therapist = super().save(commit=False)
        therapist.set_password(self.cleaned_data['password'])
        if admin_id:
            therapist.registered_by_id = admin_id
        if commit:
            therapist.save()
        return therapist
    