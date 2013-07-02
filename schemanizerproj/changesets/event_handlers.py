import logging
from django.contrib import messages
from django.utils import timezone
from emails import tasks as emails_tasks
from events import models as events_models
from changesetreviews import tasks as changesetreviews_tasks

log = logging.getLogger(__name__)


def on_changeset_submit(changeset, request=None):
    """Queues tasks for changeset submit event."""
    user = None
    if request:
        user = request.user.schemanizer_user

    msg = 'Changeset [id=%s] was submitted.' % changeset.pk
    events_models.Event.objects.create(
        datetime=timezone.now(),
        type=events_models.Event.TYPE.changeset_submitted,
        description=msg,
        user=request.user.schemanizer_user)

    emails_tasks.send_mail_changeset_submitted.delay(changeset.pk)

    if request:
        messages.success(request, msg)
    log.info(msg)

    changesetreviews_tasks.review_changeset.delay(
        changeset_pk=changeset.pk, reviewed_by_user_pk=user.pk)

    if request:
        messages.info(
            request,
            'Changeset review process has been started. The result will be '
            'emailed to interested parties once the process has completed.')


def on_changeset_approved(changeset, request=None):
    msg = 'Changeset [id=%s] was approved.' % changeset.pk
    events_models.Event.objects.create(
        datetime=timezone.now(),
        type=events_models.Event.TYPE.changeset_approved,
        description=msg,
        user=changeset.approved_by)

    if request:
        messages.success(request, msg)
    log.info(msg)

    emails_tasks.send_mail_changeset_approved.delay(changeset.pk)


def on_changeset_updated(changeset, request=None):
    user = None
    if request:
        user = request.user.schemanizer_user
    msg = 'Changeset [id=%s] was updated.' % changeset.pk
    events_models.Event.objects.create(
        datetime=timezone.now(),
        type=events_models.Event.TYPE.changeset_updated,
        description=msg,
        user=user)

    if request:
        messages.success(request, msg)
    log.info(msg)

    emails_tasks.send_mail_changeset_updated(changeset.pk)


def on_changeset_rejected(changeset, request=None):
    msg = 'Changeset [id=%s] was rejected.' % changeset.pk
    events_models.Event.objects.create(
        datetime=timezone.now(),
        type=events_models.Event.TYPE.changeset_rejected,
        description=msg,
        user=changeset.approved_by)

    if request:
        messages.success(request, msg)
    log.info(msg)

    emails_tasks.send_mail_changeset_rejected.delay(changeset.pk)


def on_changeset_soft_deleted(changeset, request=None):
    user = None
    if request:
        user = request.user.schemanizer_user

    msg = 'Changeset [id=%s] was soft deleted.' % changeset.pk
    events_models.Event.objects.create(
        datetime=timezone.now(),
        type=events_models.Event.TYPE.changeset_soft_deleted,
        description=msg,
        user=user)

    if request:
        messages.success(request, msg)
    log.info(msg)
