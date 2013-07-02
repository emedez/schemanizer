from django.contrib import admin
from . import models


class ChangesetReviewAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'changeset', 'schema_version', 'success', 'results_log',
        'task_id', 'created_at', 'updated_at')


admin.site.register(models.ChangesetReview, ChangesetReviewAdmin)
