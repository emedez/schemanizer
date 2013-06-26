from django.contrib import messages
from django.utils import timezone
from events import models


def on_user_added(request, obj):
    description = 'Added user: id=%s, name=%s' % (obj.pk, obj.name)
    models.Event.objects.create(
        datetime=timezone.now(), type=models.Event.TYPE.user_added,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)


def on_user_updated(request, obj):
    description = 'Updated user: id=%s, name=%s' % (obj.pk, obj.name)
    models.Event.objects.create(
        datetime=timezone.now(), type=models.Event.TYPE.user_updated,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)


def on_user_deleted(request, obj):
    description = 'Deleted user: id=%s, name=%s' % (obj.pk, obj.name)
    models.Event.objects.create(
        datetime=timezone.now(), type=models.Event.TYPE.user_deleted,
        description=description,
        user=request.user.schemanizer_user)
    messages.success(request, description)
