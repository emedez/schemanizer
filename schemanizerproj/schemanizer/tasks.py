"""Celery tasks."""

import logging

from celery import task

from schemanizer import models, utils
from schemanizer.logic import (
    changeset_review_logic,
    mail_logic)

log = logging.getLogger(__name__)


@task()
def review_changeset(changeset):
    """Reviews changeset."""

    log.debug('task: review_changeset')
    changeset = utils.get_model_instance(changeset, models.Changeset)
    changeset_review_logic.review_changeset(changeset)


@task()
def send_mail_changeset_reviewed(changeset):
    """Sends 'changeset reviewed' email."""

    log.debug('task: send_mail_changeset_reviewed')
    changeset = utils.get_model_instance(changeset, models.Changeset)
    mail_logic.send_mail_changeset_reviewed(changeset)