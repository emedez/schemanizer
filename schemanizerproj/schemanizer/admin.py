from django.contrib import admin

from schemanizer import models


class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'email', 'role', 'created_at', 'updated_at', 'auth_user')


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


class EnvironmentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'created_at', 'updated_at')


class ServerAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'created_at', 'updated_at', 'environment')


class ChangesetDetailApplyAdmin(admin.ModelAdmin):
    list_display = (
        'changeset_detail', 'environment', 'server', 'results_log',
        'created_at', 'updated_at')


class DatabaseSchemaAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'created_at', 'updated_at')


class SchemaVersionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'database_schema', 'ddl', 'checksum', 'created_at', 'updated_at')


class ValidationTypeAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'description', 'validation_commands', 'created_at',
        'updated_at')

class ChangesetValidationAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'changeset', 'validation_type', 'timestamp', 'result',
        'created_at', 'updated_at')

admin.site.register(models.Role, RoleAdmin)
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Changeset, ChangesetAdmin)
admin.site.register(models.Environment, EnvironmentAdmin)
admin.site.register(models.Server, ServerAdmin)
admin.site.register(models.ChangesetDetailApply, ChangesetDetailApplyAdmin)
admin.site.register(models.DatabaseSchema, DatabaseSchemaAdmin)
admin.site.register(models.SchemaVersion, SchemaVersionAdmin)
admin.site.register(models.ValidationType, ValidationTypeAdmin)
admin.site.register(models.ChangesetValidation, ChangesetValidationAdmin)
admin.site.register(models.TestType)
admin.site.register(models.ChangesetTest)
admin.site.register(models.ChangesetApply)
admin.site.register(models.ChangesetReview)