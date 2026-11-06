from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import Child


class ChildRegistrationForm(forms.ModelForm):
    """
    ModelForm for registering basic child information before assessment.
    """
    class Meta:
        model = Child
        fields = ['name', 'age', 'gender', 'grade']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': "Enter child's full name (e.g. Maya Sharma)",
                'autocomplete': 'name',
                'required': True,
            }),
            'age': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': "Age between 5 and 18",
                'min': '5',
                'max': '18',
                'required': True,
            }),
            'gender': forms.Select(attrs={
                'class': 'form-select',
                'required': True,
            }),
            'grade': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': "e.g. 5th Grade, Class 6 (Optional)",
                'autocomplete': 'off',
            }),
        }
        labels = {
            'name': "Child's Full Name",
            'age': "Age (Years)",
            'gender': "Gender Identity",
            'grade': "Grade / School Class (Optional)",
        }
        help_texts = {
            'name': "Enter the name that will appear on the assessment report.",
            'age': "Assessments are calibrated for children aged 5 to 18.",
            'gender': "Used for personalized tone and reporting balance.",
            'grade': "Helps contextualize developmental learning stages.",
        }
        error_messages = {
            'name': {
                'required': "Child's name cannot be empty.",
            },
            'age': {
                'required': "Please provide the child's age.",
            },
            'gender': {
                'required': "Please select a gender option.",
            },
        }

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError("Child's name cannot be empty.")
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        return name

    def clean_age(self):
        age = self.cleaned_data.get('age')
        if age is None:
            raise forms.ValidationError("Please provide the child's age.")
        if age < 5 or age > 18:
            raise forms.ValidationError("Age must be between 5 and 18 years.")
        return age


class MindBloomAuthenticationForm(AuthenticationForm):
    """
    Styled authentication form using Django's built-in AuthenticationForm.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your username',
            'autocomplete': 'username',
            'autofocus': True,
        }),
        label="Username"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        }),
        label="Password"
    )


class UserRegistrationForm(UserCreationForm):
    """
    Registration form for parents and educators creating a MindBloom account.
    Extends Django's native UserCreationForm with email and full name.
    """
    first_name = forms.CharField(
        max_length=50,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Your Full Name (e.g. Priya Sharma)',
            'autocomplete': 'name',
        }),
        label="Full Name"
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-input',
            'placeholder': 'Email address (e.g. parent@example.com)',
            'autocomplete': 'email',
        }),
        label="Email Address"
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ['username', 'first_name', 'email']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Choose a unique username',
                'autocomplete': 'username',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password1' in self.fields:
            self.fields['password1'].widget.attrs.update({
                'class': 'form-input',
                'placeholder': 'Create password (min. 8 characters)',
            })
        if 'password2' in self.fields:
            self.fields['password2'].widget.attrs.update({
                'class': 'form-input',
                'placeholder': 'Confirm password',
            })
        for f in self.fields.values():
            f.widget.attrs.setdefault('class', 'form-input')
