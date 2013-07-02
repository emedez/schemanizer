from django.contrib import admin
from . import models


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
        'review_version',
        'before_version',
        'after_version',
        'repo_filename',
        'created_at', 'updated_at',
    )

    inlines = (ChangesetDetailInline, ChangesetActionInline)


class ChangesetActionAdmin(admin.ModelAdmin):
    list_display = ('id', 'changeset', 'type', 'timestamp')


class ChangesetActionServerMapAdmin(admin.ModelAdmin):
    list_display = ('id', 'changeset_action', 'server')


admin.site.register(models.Changeset, ChangesetAdmin)
admin.site.register(models.ChangesetAction, ChangesetActionAdmin)
admin.site.register(
    models.ChangesetActionServerMap, ChangesetActionServerMapAdmin)