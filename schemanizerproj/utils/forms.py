from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit


class SubmitForm(forms.Form):
    """Form that contains submit button only."""

    def __init__(self, *args, **kwargs):
        super(SubmitForm, self).__init__(*args, **kwargs)

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('submit', 'Submit'))
        self.helper = helper

