from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import UserProfile

class CustomUserForm(UserCreationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter User Name'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter User Email'
        })
    )
    contact_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter Contact Number'
        }),
        help_text="Enter your phone number with country code (e.g., +1234567890)"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2','contact_number']
        
    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        self.fields['password1'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter User Password'}
        )
        self.fields['password2'].widget = forms.PasswordInput(
            attrs={'class': 'form-control', 'placeholder': 'Enter User Confirm Password'}
        )
    
    # def clean_contact_number(self):
        # contact_number = self.cleaned_data.get('contact_number')
        # if UserProfile.objects.filter(contact_number=contact_number).exists():
            # raise forms.ValidationError("This contact number is already registered.")
        # return contact_number
