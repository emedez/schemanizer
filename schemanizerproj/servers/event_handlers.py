from django.contrib import messages
from django.utils import timezone
from events import models


def on_environment_added(request, obj):
    description = 'Added environment: id=%s, name=%s' % (obj.pk, obj.name)
    models.Event.objects.create(
        datetime=timezone.now(), type=models.Event.TYPE.environment_added,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)


def on_environment_updated(request, obj):
    description = 'Updated environment: id=%s, name=%s' % (obj.pk, obj.name)
    models.Event.objects.create(
        datetime=timezone.now(), type=models.Event.TYPE.environment_updated,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)


def on_environment_deleted(request, obj):
    description = 'Deleted environment: id=%s, name=%s' % (obj.pk, obj.name)
    models.Event.objects.create(
        datetime=timezone.now(), type=models.Event.TYPE.environment_deleted,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)


def on_server_added(request, obj):
    description = 'Added server: id=%s, name=%s' % (obj.pk, obj.name)
    models.Event.objects.create(
        datetime=timezone.now(), type=models.Event.TYPE.server_added,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)


def on_server_updated(request, obj):
    description = 'Updated server: id=%s, name=%s' % (obj.pk, obj.name)
    models.Event.objects.create(
        datetime=timezone.now(), type=models.Event.TYPE.server_updated,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)


def on_server_deleted(request, obj):
    description = (
        'Deleted server: id=%s, name=%s, hostname=%s, port=%s, '
        'environment=%s' % (
            obj.id, obj.name, obj.hostname, obj.port, obj.environment))
    models.Event.objects.create(
        datetime=timezone.now(), type=models.Event.TYPE.server_deleted,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)