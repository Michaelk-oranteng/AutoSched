from django import forms
from .models import University, UserProfile, Program


class SignupForm(forms.Form):
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'signup-input', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'signup-input', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'signup-input', 'placeholder': 'Email Address'})
    )
    contact = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'signup-input', 'placeholder': 'Contact Number'})
    )
    institution = forms.ModelChoiceField(
        queryset=University.objects.all().order_by('name'),
        empty_label="Select your University",
        widget=forms.Select(attrs={'class': 'signup-input'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'signup-input', 'placeholder': 'Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'signup-input', 'placeholder': 'Confirm Password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords do not match.")

        return cleaned_data

   
class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'placeholder': 'Enter Email',
        'class': 'login-input'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'placeholder': 'Enter Password',
        'class': 'login-input'
    }))
    
class ResetForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'signup-input',
            'placeholder': 'email@institution.edu',
            'id': 'id_email'
        })
    )
    

class ProgramForm(forms.Form):
    AcademicLevel = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'signup-input', 'placeholder': 'First Name'})
    )
    ProgramLevel = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'signup-input', 'placeholder': 'First Name'})
    )
    SpecilizationName = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'signup-input', 'placeholder': 'First Name'})
    )