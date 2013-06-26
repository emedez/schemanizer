from django.contrib import admin
from . import models


class DatabaseSchemaAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'created_at', 'updated_at')


class SchemaVersionAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'database_schema', 'ddl', 'checksum', 'pulled_from',
        'pull_datetime', 'created_at', 'updated_at')


admin.site.register(models.DatabaseSchema, DatabaseSchemaAdmin)
admin.site.register(models.SchemaVersion, SchemaVersionAdmin)

