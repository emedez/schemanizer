import logging

from django.contrib.auth.forms import AuthenticationForm as BuiltinAuthenticationForm
from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit

from schemanizer import models

log = logging.getLogger(__name__)


class AuthenticationForm(BuiltinAuthenticationForm):
    def __init__(self, *args, **kwargs):
        super(AuthenticationForm, self).__init__(*args, **kwargs)

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('submit', 'Login'))
        self.helper = helper


class ChangesetForm(forms.ModelForm):
    class Meta:
        model = models.Changeset
        fields = ('type', 'classification', 'version_control_url')

    def __init__(self, *args, **kwargs):
        super(ChangesetForm, self).__init__(*args, **kwargs)

        self.fields['type'].required = True
        self.fields['classification'].required = True
        self.fields['version_control_url'].required = True

        helper = FormHelper()
        helper.form_tag = False
        self.helper = helper


class ChangesetDetailForm(forms.ModelForm):
    class Meta:
        model = models.ChangesetDetail

    def __init__(self, *args, **kwargs):
        super(ChangesetDetailForm, self).__init__(*args, **kwargs)

        self.fields['type'].required = True
        self.fields['description'].widget.attrs.update(dict(rows=2))
        self.fields['apply_sql'].widget.attrs.update(dict(rows=2))
        self.fields['revert_sql'].widget.attrs.update(dict(rows=2))
        self.fields['count_sql'].widget.attrs.update(dict(rows=2))
        self.fields['volumetric_values'].widget.attrs.update(dict(rows=2))

        helper = FormHelper()
        helper.form_tag = False
        self.helper = helper
