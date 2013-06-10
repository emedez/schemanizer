"""Celery tasks."""
import functools
import logging
import time

from celery import current_task, states, task

from schemanizer import models, utils
from schemanizer.logic import (
    changeset_review_logic,
    mail_logic)

log = logging.getLogger(__name__)


@task()
def review_changeset(changeset, schema_version=None, user=None):
    """Reviews changeset."""

    log.debug('task: review_changeset')
    def message_callback(message, message_type, current_task):
        log.debug('message_callback = %s', message)
        current_task.update_state(
            state=states.STARTED,
            meta={
                'message': {
                    'text': message,
                    'type': message_type
                }
            })
    message_callback=functools.partial(
        message_callback, current_task=current_task)
    changeset = utils.get_model_instance(changeset, models.Changeset)
    changeset_review_logic.review_changeset(
        changeset, schema_version, user, message_callback=message_callback)
    current_task.update_state(state=states.STARTED, meta={'message': 'done'})
    time.sleep(60)

@task()
def send_mail_changeset_reviewed(changeset):
    """Sends 'changeset reviewed' email."""

    log.debug('task: send_mail_changeset_reviewed')
    changeset = utils.get_model_instance(changeset, models.Changeset)
    mail_logic.send_mail_changeset_reviewed(changeset)


@task()
def long_task_test(a=None, b=None):
    log.debug('long task test started')
    log.debug('a = %s, b = %s', a, b)
    current_task.update_state(state='LONG_TASK_TEST_STARTED', meta=dict(var1='one', var2='two'))
    time.sleep(600)
    current_task.update_state(state='LONG_TASK_TEST_COMPLETED')
    log.debug('long task test ended')
