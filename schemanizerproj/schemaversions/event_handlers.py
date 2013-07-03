from django.contrib import messages
from django.utils import timezone
from events import models as events_models


def on_schema_version_generated(request, obj, created):
    description = (
        'Generated schema version [id=%s, database_schema=%s, '
        'pulled_from=%s].' % (
            obj.pk, obj.database_schema.name, obj.pulled_from))
    events_models.Event.objects.create(
        datetime=timezone.now(),
        type=events_models.Event.TYPE.schema_version_generated,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)


def on_schema_check(request, database_schema):
    description = 'Schema check was performed for database schema \'%s\'.' % (
        database_schema.name,)
    events_models.Event.objects.create(
        datetime=timezone.now(),
        type=events_models.Event.TYPE.schema_check,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)