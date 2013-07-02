from crispy_forms.helper import FormHelper
from django import forms
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