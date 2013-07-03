import logging
from celery import task
from changesetapplies import models as changesetapplies_models
from changesets import models as changesets_models
from . import email_functions

log = logging.getLogger(__name__)


@task(ignore_result=True)
def send_mail_changeset_submitted(changeset_pk):
    try:
        changeset = changesets_models.Changeset.objects.get(pk=changeset_pk)
        email_functions.send_mail_changeset_submitted(changeset)
    except:
        log.exception('EXCEPTION')
        raise


@task(ignore_result=True)
def send_mail_changeset_reviewed(changeset_pk):
    """Sends 'changeset reviewed' email."""
    try:
        changeset = changesets_models.Changeset.objects.get(pk=changeset_pk)
        email_functions.send_mail_changeset_reviewed(changeset)
    except:
        log.exception('EXCEPTION')
        raise


@task(ignore_result=True)
def send_mail_changeset_approved(changeset_pk):
    try:
        changeset = changesets_models.Changeset.objects.get(pk=changeset_pk)
        email_functions.send_mail_changeset_approved(changeset)
    except:
        log.exception('EXCEPTION')
        raise


@task(ignore_result=True)
def send_mail_changeset_updated(changeset_pk):
    try:
        changeset = changesets_models.Changeset.objects.get(pk=changeset_pk)
        email_functions.send_mail_changeset_updated(changeset)
    except:
        log.exception('EXCEPTION')
        raise


@task(ignore_result=True)
def send_mail_changeset_rejected(changeset_pk):
    try:
        changeset = changesets_models.Changeset.objects.get(pk=changeset_pk)
        email_functions.send_mail_changeset_rejected(changeset)
    except:
        log.exception('EXCEPTION')
        raise


@task(ignore_result=True)
def send_mail_changeset_applied(changeset_apply_pk):
    try:
        changeset_apply = changesetapplies_models.ChangesetApply.objects.get(
            pk=changeset_apply_pk)
        email_functions.send_mail_changeset_applied(changeset_apply)
    except:
        log.exception('EXCEPTION')
        raise


@task(ignore_result=True)
def send_changeset_submission_through_repo_failed_mail(
        changeset_content, error_message, file_data, commit_data):
    """Task for sending changeset-submission-through-repo-failed email."""
    try:
        email_functions.send_changeset_submission_through_repo_failed_mail(
            changeset_content, error_message, file_data, commit_data)
    except:
        log.exception('EXCEPTION')
        raise