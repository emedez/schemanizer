import logging
from django.contrib import messages
from django.utils import timezone
from emails import tasks as emails_tasks
from events import models as events_models

log = logging.getLogger(__name__)


def on_changeset_reviewed(changeset, request=None):
    user = None
    if request:
        user = request.user.schemanizer_user
    if not user:
        user = changeset.reviewed_by

    msg = u'Changeset [id=%s] was reviewed.' % changeset.pk

    events_models.Event.objects.create(
        datetime=timezone.now(),
        type=events_models.Event.TYPE.changeset_reviewed,
        description=msg,
        user=user)

    if request:
        messages.success(request, msg)

    log.info(msg)

    emails_tasks.send_mail_changeset_reviewed.delay(changeset.pk)


