from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, Profile, LeaveRequest
import re


class SignUpForm(UserCreationForm):
    """Custom sign-up form with employee ID and role"""
    first_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        max_length=30, 
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Last Name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email Address'
        })
    )
    employee_id = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Employee ID (e.g., EMP1234)'
        }),
        help_text='Format: EMP followed by 4-6 digits'
    )
    role = forms.ChoiceField(
        choices=CustomUser.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['employee_id', 'first_name', 'last_name', 'email', 'role', 'username', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Username'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Confirm Password'
        })
    
    def clean_employee_id(self):
        """Validate employee ID format"""
        employee_id = self.cleaned_data.get('employee_id')
        if not re.match(r'^EMP\d{4,6}$', employee_id):
            raise ValidationError('Employee ID must be in format: EMP1234 (EMP followed by 4-6 digits)')
        
        if CustomUser.objects.filter(employee_id=employee_id).exists():
            raise ValidationError('This Employee ID is already registered.')
        
        return employee_id
    
    def clean_email(self):
        """Validate email uniqueness"""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email


class SignInForm(AuthenticationForm):
    """Custom sign-in form with styled widgets"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Username or Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Password'
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    """Form for employees to update their profile"""
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'emergency_contact', 'profile_picture']
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Phone Number'
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Address',
                'rows': 3
            }),
            'emergency_contact': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Emergency Contact Number'
            }),
            'profile_picture': forms.FileInput(attrs={
                'class': 'form-file-input'
            })
        }


class AdminProfileUpdateForm(forms.ModelForm):
    """Form for admins to update any employee profile"""
    class Meta:
        model = Profile
        fields = ['designation', 'department', 'date_of_joining', 'employment_type', 
                  'phone_number', 'address', 'emergency_contact']
        widgets = {
            'designation': forms.TextInput(attrs={'class': 'form-input'}),
            'department': forms.TextInput(attrs={'class': 'form-input'}),
            'date_of_joining': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'employment_type': forms.Select(attrs={'class': 'form-select'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'emergency_contact': forms.TextInput(attrs={'class': 'form-input'}),
        }


class LeaveRequestForm(forms.ModelForm):
    """Form for employees to request leave"""
    class Meta:
        model = LeaveRequest
        fields = ['leave_type', 'start_date', 'end_date', 'remarks']
        widgets = {
            'leave_type': forms.Select(attrs={'class': 'form-select'}),
            'start_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-input',
                'type': 'date'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Reason for leave',
                'rows': 4
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise ValidationError('End date must be after start date.')
        
        return cleaned_data
