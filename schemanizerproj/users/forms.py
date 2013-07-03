from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from . import models


class UserAddForm(forms.Form):
    """Form for adding users."""

    name = forms.CharField(max_length=255)
    email = forms.EmailField(max_length=255)
    role = forms.ChoiceField()
    github_login = forms.CharField(max_length=255, required=False)
    password = forms.CharField(max_length=30, widget=forms.PasswordInput)
    confirm_password = forms.CharField(max_length=30, widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(UserAddForm, self).__init__(*args, **kwargs)

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


class UserUpdateForm(forms.Form):
    """Form for updating users."""

    name = forms.CharField(max_length=255)
    email = forms.EmailField(max_length=255)
    role = forms.ChoiceField()
    github_login = forms.CharField(max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)

        role_qs = models.Role.objects.all()
        role_choices = []
        for role in role_qs:
            role_choices.append((role.id, role.name))
        self.fields['role'].choices = role_choices

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('submit', 'Save'))
        self.helper = helper