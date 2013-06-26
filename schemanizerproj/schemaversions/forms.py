from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms


class SchemaVersionGenerateForm(forms.Form):
    schema = forms.ChoiceField(help_text='System databases not displayed.')

    def __init__(self, *args, **kwargs):
        super(SchemaVersionGenerateForm, self).__init__(*args, **kwargs)

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('submit', 'Submit'))
        self.helper = helper


class SchemaVersionActionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(SchemaVersionActionsForm, self).__init__(*args, **kwargs)

        helper = FormHelper()
        helper.form_class = 'form-inline'
        helper.add_input(Submit('schema_check', 'Schema Check'))
        self.helper = helper