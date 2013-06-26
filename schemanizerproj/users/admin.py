from django.contrib import admin
from . import models


class RoleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')


class UserAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'email', 'role', 'auth_user', 'created_at',
        'updated_at')


admin.site.register(models.Role, RoleAdmin)
admin.site.register(models.User, UserAdmin)