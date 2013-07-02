"""Celery tasks."""
import logging
import time

from celery import current_task, task

from schemanizer.logic import (
    mail_logic)

log = logging.getLogger(__name__)


@task(ignore_result=True)
def send_changeset_submission_through_repo_failed_mail(
        changeset_content, error_message, file_data, commit_data):
    """Task for sending changeset-submission-through-repo-failed email."""
    mail_logic.send_changeset_submission_through_repo_failed_mail(
        changeset_content, error_message, file_data, commit_data)











@task()
def testtask(start_value=0, end_value=10, step=1):
    current_value = start_value
    while current_value < end_value:
        current_value += step
        current_task.update_state(state='IN_PROGRESS', meta=dict(current_value=current_value))
        time.sleep(10)

    return 'final result'