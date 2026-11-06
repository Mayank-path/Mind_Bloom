from django import forms
from core.forms import ChildRegistrationForm
from .models import Answer


class QuestionAnswerForm(forms.Form):
    """
    Form for selecting an option (A, B, C, D) for the active question.
    """
    selected_option = forms.ChoiceField(
        choices=Answer.OptionChoice.choices,
        widget=forms.RadioSelect(attrs={'class': 'sr-only'}),
        required=True,
        error_messages={
            'required': 'Please choose an option to continue.',
        }
    )


__all__ = ['ChildRegistrationForm', 'QuestionAnswerForm']
