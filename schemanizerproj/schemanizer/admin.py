from django.contrib import admin

from schemanizer import models


class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'email', 'role', 'created_at', 'updated_at', 'user')


class ChangesetDetailInline(admin.TabularInline):
    model = models.ChangesetDetail


class ChangesetActionInline(admin.TabularInline):
    model = models.ChangesetAction


class ChangesetAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'type', 'classification', 'version_control_url',
        'review_status', 'reviewed_by', 'reviewed_at',
        'approved_by', 'approved_at',
        'submitted_by', 'submitted_at',
        'created_at', 'updated_at'
    )

    inlines = (ChangesetDetailInline, ChangesetActionInline)


admin.site.register(models.Role, RoleAdmin)
admin.site.register(models.User, UserAdmin)
admin.site.register(models.Changeset, ChangesetAdmin)
