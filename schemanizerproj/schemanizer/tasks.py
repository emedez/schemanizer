"""Celery tasks."""
import functools
import logging
import time

from celery import current_task, states, task

from schemanizer import models, utils
from schemanizer.logic import (
    changeset_apply_logic,
    changeset_review_logic,
    mail_logic)

log = logging.getLogger(__name__)


@task(ignore_result=True)
def send_changeset_submission_through_repo_failed_mail(
        changeset_content, error_message, file_data, commit_data):
    """Task for sending changeset-submission-through-repo-failed email."""
    mail_logic.send_changeset_submission_through_repo_failed_mail(
        changeset_content, error_message, file_data, commit_data)


@task(ignore_result=True)
def review_changeset(changeset, schema_version=None, user=None):
    """Reviews changeset."""
    def message_callback(message, message_type, current_task):
        current_task.update_state(
            state=states.STARTED,
            meta=dict(
                message=message,
                message_type=message_type))

    message_callback = functools.partial(
        message_callback, current_task=current_task)
    changeset = utils.get_model_instance(changeset, models.Changeset)
    changeset_review_logic.review_changeset(
        changeset, schema_version, user, message_callback=message_callback)

    # TODO: remove when no longer needed
    # Simulate long running task by sleeping
    #time.sleep(30)

    current_task.update_state(
        state=states.STARTED,
        meta=dict(
            message='Changeset review job completed.',
            message_type='info'))


@task(ignore_result=True)
def apply_changeset(changeset_id, user_id, server_id):
    """Applies changeset."""

    messages = []

    current_task.update_state(
        state=states.STARTED,
        meta=dict(
            changeset_id=changeset_id,
            user_id=user_id,
            server_id=server_id,
            messages=messages
        ))

    def message_callback(message, message_type, extra=None):
        messages.append(dict(
            message=message,
            message_type=message_type,
            extra=extra))
        current_task.update_state(
            state=states.STARTED,
            meta=dict(
                changeset_id=changeset_id,
                user_id=user_id,
                server_id=server_id,
                messages=messages))

    changeset_apply_obj = changeset_apply_logic.apply_changeset(
        changeset_id, user_id, server_id, message_callback)

    messages.append(dict(
        message='Changeset apply job completed.',
        message_type='info',
        extra=None))

    current_task.update_state(
        state=states.STARTED,
        meta=dict(
            changeset_id=changeset_id,
            user_id=user_id,
            server_id=server_id,
            messages=messages,
            changeset_detail_apply_ids=
                changeset_apply_obj.changeset_detail_apply_ids))


@task()
def send_mail_changeset_reviewed(changeset):
    """Sends 'changeset reviewed' email."""

    log.debug('task: send_mail_changeset_reviewed')
    changeset = utils.get_model_instance(changeset, models.Changeset)
    mail_logic.send_mail_changeset_reviewed(changeset)


@task()
def testtask(start_value=0, end_value=10, step=1):
    current_value = start_value
    while current_value < end_value:
        current_value += step
        current_task.update_state(state='IN_PROGRESS', meta=dict(current_value=current_value))
        time.sleep(10)

    return 'final result'