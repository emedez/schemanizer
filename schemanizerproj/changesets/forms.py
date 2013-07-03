from crispy_forms.helper import FormHelper
from django import forms
from schemaversions import models as schemaversions_models
from . import models


class ChangesetForm(forms.ModelForm):
    class Meta:
        model = models.Changeset
        fields = (
            'database_schema', 'type', 'classification',
            'review_version'
        )

    def __init__(self, *args, **kwargs):
        super(ChangesetForm, self).__init__(*args, **kwargs)

        helper = FormHelper()
        helper.form_tag = False
        self.helper = helper

    def clean(self):
        cleaned_data = super(ChangesetForm, self).clean()

        database_schema = cleaned_data.get('database_schema')
        review_version = cleaned_data.get('review_version')

        if database_schema and review_version:
            if database_schema.pk != review_version.database_schema.pk:
                raise forms.ValidationError(
                    'Invalid schema version, it should be related to the '
                    'selected database schema.')

        return cleaned_data


class ChangesetNoReviewVersionForm(forms.ModelForm):
    class Meta:
        model = models.Changeset
        fields = (
            'database_schema', 'type', 'classification'
        )

    def __init__(self, *args, **kwargs):
        super(ChangesetNoReviewVersionForm, self).__init__(*args, **kwargs)

        helper = FormHelper()
        helper.form_tag = False
        self.helper = helper


class ChangesetDetailForm(forms.ModelForm):
    class Meta:
        model = models.ChangesetDetail
        fields = ('changeset', 'description', 'apply_sql', 'revert_sql',
            'apply_verification_sql', 'revert_verification_sql')

    def __init__(self, *args, **kwargs):
        super(ChangesetDetailForm, self).__init__(*args, **kwargs)

        for fld_name, fld in self.fields.iteritems():
            if isinstance(fld.widget, forms.Textarea):
                fld.widget.attrs.update(
                    {'rows': '4', 'cols': '80', 'class': 'form-textarea'})

        helper = FormHelper()
        helper.form_tag = False
        self.helper = helper