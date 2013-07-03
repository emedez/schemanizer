from django.contrib import admin

from . import models


class EnvironmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')


class ServerAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'name', 'hostname', 'port', 'environment', 'created_at',
        'updated_at')


class ServerDataAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'server', 'database_schema', 'schema_exists', 'schema_version',
        'schema_version_diff', 'created_at', 'updated_at')


admin.site.register(models.Environment, EnvironmentAdmin)
admin.site.register(models.Server, ServerAdmin)
admin.site.register(models.ServerData, ServerDataAdmin)



