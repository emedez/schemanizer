import logging
from django.contrib import messages
from django.utils import timezone
from emails import tasks as emails_tasks
from events import models as events_models

log = logging.getLogger(__name__)


def on_changeset_applied(changeset_apply, request=None):
    msg = u'Changeset [id=%s] was applied at server [id=%s, name=%s].' % (
        changeset_apply.changeset.pk,
        changeset_apply.server.pk,
        changeset_apply.server.name)

    events_models.Event.objects.create(
        datetime=timezone.now(),
        type=events_models.Event.TYPE.changeset_applied,
        description=msg,
        user=changeset_apply.applied_by)

    if request:
        messages.success(request, msg)

    log.info(msg)

    emails_tasks.send_mail_changeset_applied.delay(changeset_apply.pk)


def on_changeset_apply_failed(changeset_apply, request=None):

    msg = u'Failed to apply changeset [id=%s] at server [id=%s, name=%s].' % (
        changeset_apply.changeset.pk,
        changeset_apply.server.pk,
        changeset_apply.server.name)

    events_models.Event.objects.create(
        datetime=timezone.now(),
        type=events_models.Event.TYPE.changeset_apply_failed,
        description=msg,
        user=changeset_apply.applied_by)

    if request:
        messages.success(request, msg)

    log.info(msg)
