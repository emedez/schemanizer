from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from . import models


class ServerForm(forms.ModelForm):
    class Meta:
        model = models.Server

    def __init__(self, *args, **kwargs):
        super(ServerForm, self).__init__(*args, **kwargs)

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('submit', 'Submit'))
        self.helper = helper


class EnvironmentForm(forms.ModelForm):
    class Meta:
        model = models.Environment

    def __init__(self, *args, **kwargs):
        super(EnvironmentForm, self).__init__(*args, **kwargs)

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('submit', 'Submit'))
        self.helper = helper