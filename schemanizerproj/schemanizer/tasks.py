"""Celery tasks."""
import logging
import time

from celery import current_task, task


log = logging.getLogger(__name__)














@task()
def testtask(start_value=0, end_value=10, step=1):
    current_value = start_value
    while current_value < end_value:
        current_value += step
        current_task.update_state(state='IN_PROGRESS', meta=dict(current_value=current_value))
        time.sleep(10)

    return 'final result'