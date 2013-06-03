"""Celery tasks."""

import logging

from celery import task

from schemanizer import models, utils
from schemanizer.logic import mail_logic

log = logging.getLogger(__name__)


@task()
def review_changeset(changeset):
    log.debug('task: review_changeset')
    changeset = utils.get_model_instance(changeset, models.Changeset)
    mail_logic.send_changeset_submitted_mail(changeset)
