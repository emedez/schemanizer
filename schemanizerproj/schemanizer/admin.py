from django.contrib import admin

from schemanizer import models
from users.admin import UserAdmin
from users.models import User


class ChangesetDetailInline(admin.TabularInline):
    model = models.ChangesetDetail


class ChangesetActionInline(admin.TabularInline):
    model = models.ChangesetAction


class ChangesetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'database_schema', 'type', 'classification',
        'version_control_url',
        'review_status', 'reviewed_by', 'reviewed_at',
        'approved_by', 'approved_at',
        'submitted_by', 'submitted_at',
        'repo_filename',
        'created_at', 'updated_at',
    )

    inlines = (ChangesetDetailInline, ChangesetActionInline)


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

admin.site.register(models.Changeset, ChangesetAdmin)
admin.site.register(models.ChangesetDetailApply, ChangesetDetailApplyAdmin)
admin.site.register(models.ValidationType, ValidationTypeAdmin)
admin.site.register(models.ChangesetValidation, ChangesetValidationAdmin)
admin.site.register(models.TestType)
admin.site.register(models.ChangesetTest)
admin.site.register(models.ChangesetApply)
admin.site.register(models.ChangesetReview)