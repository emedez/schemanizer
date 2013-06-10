import logging

from django.contrib.auth.forms import AuthenticationForm as BuiltinAuthenticationForm
from django import forms

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Button

from schemanizer import models

log = logging.getLogger(__name__)


class ContinueForm(forms.Form):
    """Form that contains submit button only."""

    def __init__(self, *args, **kwargs):
        super(ContinueForm, self).__init__(*args, **kwargs)

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('continue_form_submit', u'Continue'))
        self.helper = helper


class SelectSchemaVersionForm(forms.Form):
    """Form for selecting schema version."""
    schema_version = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        database_schema = kwargs.pop('database_schema')
        if type(database_schema) in (int, long):
            database_schema = models.DatabaseSchema.objects.get(
                pk=database_schema)
        super(SelectSchemaVersionForm, self).__init__(*args, **kwargs)

        choices = []
        for sv in database_schema.schema_versions.all().order_by('created_at'):
            choices.append((
                sv.id,
                u'ID: %s, Created at: %s, Updated at: %s' % (
                    sv.id, sv.created_at, sv.updated_at)))
        self.fields['schema_version'].choices = choices

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('select_schema_version_form_submit', 'Submit'))
        self.helper = helper


class UpdateUserForm(forms.Form):
    """Form for updating users."""

    name = forms.CharField(max_length=255)
    email = forms.EmailField(max_length=255)
    role = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(UpdateUserForm, self).__init__(*args, **kwargs)

        role_qs = models.Role.objects.all()
        role_choices = []
        for role in role_qs:
            role_choices.append((role.id, role.name))
        self.fields['role'].choices = role_choices

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('submit', 'Save'))
        self.helper = helper


class CreateUserForm(forms.Form):
    """Form for creating users."""

    name = forms.CharField(max_length=255)
    email = forms.EmailField(max_length=255)
    role = forms.ChoiceField()
    password = forms.CharField(max_length=30, widget=forms.PasswordInput)
    confirm_password = forms.CharField(max_length=30, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(CreateUserForm, self).__init__(*args, **kwargs)

        role_qs = models.Role.objects.all()
        role_choices = []
        for role in role_qs:
            role_choices.append((role.id, role.name))
        self.fields['role'].choices = role_choices

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('submit', 'Save'))
        self.helper = helper

    def clean(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password != confirm_password:
            raise forms.ValidationError(u'Passwords don\'t match')
        return self.cleaned_data


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
        fields = ('database_schema', 'type', 'classification', 'version_control_url')

    def __init__(self, *args, **kwargs):
        super(ChangesetForm, self).__init__(*args, **kwargs)

        self.fields['database_schema'].required = True
        self.fields['type'].required = True
        self.fields['classification'].required = True

        helper = FormHelper()
        helper.form_tag = False
        self.helper = helper


class ChangesetDetailForm(forms.ModelForm):
    class Meta:
        model = models.ChangesetDetail
        exclude = ('before_checksum', 'after_checksum', 'volumetric_values')

    def __init__(self, *args, **kwargs):
        super(ChangesetDetailForm, self).__init__(*args, **kwargs)

        for fld_name, fld in self.fields.iteritems():
            if isinstance(fld.widget, forms.Textarea):
                fld.widget.attrs.update({'rows': '4', 'cols': '80', 'class': 'form-textarea'})

        helper = FormHelper()
        helper.form_tag = False
        self.helper = helper


class ServerForm(forms.ModelForm):
    """Server form."""

    class Meta:
        model = models.Server

    def __init__(self, *args, **kwargs):
        super(ServerForm, self).__init__(*args, **kwargs)

        self.fields['name'].required = True

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit(u'server_form_submit', u'Submit'))
        self.helper = helper


class SelectRemoteSchemaForm(forms.Form):
    """Form for selecting remote schema."""

    schema = forms.ChoiceField(help_text='System Databases Not Displayed')

    def __init__(self, *args, **kwargs):
        super(SelectRemoteSchemaForm, self).__init__(*args, **kwargs)

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('select_remote_schema_form_submit', 'Submit'))
        self.helper = helper


class EnvironmentForm(forms.ModelForm):
    """Environment form."""

    class Meta:
        model = models.Environment

    def __init__(self, *args, **kwargs):
        super(EnvironmentForm, self).__init__(*args, **kwargs)

        self.fields['name'].required = True

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit(u'environment_form_submit', u'Submit'))
        self.helper = helper


class SelectServerForm(forms.Form):
    """Form for selecting server."""

    server = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(SelectServerForm, self).__init__(*args, **kwargs)

        qs = models.Server.objects.all().order_by('name')
        choices = []
        for r in qs:
            choices.append((r.id, u'%s [%s]' % (r.name, r.hostname)))
        self.fields['server'].choices = choices

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('select_server_form_submit', 'Submit'))
        self.helper = helper
