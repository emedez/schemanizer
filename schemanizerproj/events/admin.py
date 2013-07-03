from django.contrib import admin

from . import models


class EventAdmin(admin.ModelAdmin):
    list_display = ('id', 'datetime', 'type', 'description', 'user')


admin.site.register(models.Event, EventAdmin)