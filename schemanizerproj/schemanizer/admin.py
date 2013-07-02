from django.contrib import admin
from changesetapplies.models import ChangesetDetailApply, ChangesetApply
from changesetreviews.models import ChangesetReview
from changesets.models import Changeset, ChangesetDetail, ChangesetAction
from changesettests.models import TestType, ChangesetTest
from changesetvalidations.models import ValidationType, ChangesetValidation

from schemanizer import models
from users.admin import UserAdmin
from users.models import User





class ChangesetDetailApplyAdmin(admin.ModelAdmin):
    list_display = (
        'changeset_detail', 'environment', 'server', 'results_log',
        'created_at', 'updated_at')


class ValidationTypeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'description', 'validation_commands', 'created_at',
        'updated_at')

class ChangesetValidationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'changeset', 'validation_type', 'timestamp', 'result',
        'created_at', 'updated_at')

admin.site.register(ChangesetDetailApply, ChangesetDetailApplyAdmin)
admin.site.register(ValidationType, ValidationTypeAdmin)
admin.site.register(ChangesetValidation, ChangesetValidationAdmin)
admin.site.register(TestType)
admin.site.register(ChangesetTest)
admin.site.register(ChangesetApply)
