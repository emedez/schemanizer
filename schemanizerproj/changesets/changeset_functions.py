import logging
import pprint
from django.db import transaction
from django.utils import timezone
from emails import email_functions
from schemaversions import models as schemaversions_models
from users import models as users_models
from utils import exceptions
from . import event_handlers, models
from schemanizer.logic import privileges_logic

log = logging.getLogger(__name__)


def submit_changeset(
        from_form=True, changeset_form=None, changeset_detail_formset=None,
        submitted_by=None, request=None):
    changeset = changeset_form.save(commit=False)
    changeset.submitted_by = submitted_by
    changeset.submitted_at = timezone.now()
    changeset.save()
    changeset_form.save_m2m()
    changeset_detail_formset.save()

    models.ChangesetAction.objects.create(
        changeset=changeset,
        type=models.ChangesetAction.TYPE_CREATED,
        timestamp=timezone.now())

    event_handlers.on_changeset_submit(changeset, request)

    return changeset


def approve_changeset(changeset, approved_by, request=None):
    """Approves changeset."""

    if privileges_logic.UserPrivileges(approved_by).can_approve_changeset(
            changeset):

        #
        # Update changeset
        #
        changeset.review_status = models.Changeset.REVIEW_STATUS_APPROVED
        changeset.approved_by = approved_by
        changeset.approved_at = timezone.now()
        changeset.save()

        #
        # Create changeset action entry.
        #
        models.ChangesetAction.objects.create(
            changeset=changeset,
            type=models.ChangesetAction.TYPE_APPROVED,
            timestamp=timezone.now())

        event_handlers.on_changeset_approved(
            changeset=changeset, request=request)

        return changeset

    else:
        raise exceptions.PrivilegeError(
            u'User is not allowed to approve changeset.')


def update_changeset(
        from_form=True, changeset_form=None, changeset_detail_formset=None,
        updated_by=None, request=None):

    if not updated_by and request:
        updated_by = request.user.schemanizer_user

    changeset = changeset_form.save(commit=False)
    if privileges_logic.UserPrivileges(updated_by).can_update_changeset(changeset):
        #
        # Update changeset
        #
        changeset.review_status = changeset.REVIEW_STATUS_NEEDS
        changeset.save()
        changeset_form.save_m2m()
        #
        # Save changeset details
        changeset_detail_formset.save()
        #
        # Create entry on changeset actions
        models.ChangesetAction.objects.create(
            changeset=changeset,
            type=models.ChangesetAction.TYPE_CHANGED,
            timestamp=timezone.now())

        event_handlers.on_changeset_updated(changeset, request)

    else:
        raise exceptions.PrivilegeError(
            u'User is not allowed to update changeset.')

    return changeset


def reject_changeset(changeset, rejected_by, request=None):
    """Rejects changeset."""


    if privileges_logic.UserPrivileges(rejected_by).can_reject_changeset(changeset):
        #
        # Update changeset.
        #
        changeset.review_status = models.Changeset.REVIEW_STATUS_REJECTED
        changeset.approved_by = rejected_by
        changeset.approved_at = timezone.now()
        changeset.save()
        #
        # Create changeset actions entry.
        models.ChangesetAction.objects.create(
            changeset=changeset,
            type=models.ChangesetAction.TYPE_REJECTED,
            timestamp=timezone.now())

        event_handlers.on_changeset_rejected(changeset, request)

        return changeset

    else:
        log.debug(
            u'changeset:\n%s\n\nuser=%s' % (changeset, rejected_by.name))
        raise exceptions.PrivilegeError(
            u'User is not allowed to reject changeset.')


def soft_delete_changeset(changeset, user=None, request=None):
    """Soft deletes changeset."""

    privileges_logic.UserPrivileges(user).check_soft_delete_changeset(
        changeset)

    changeset.is_deleted = True
    changeset.save()

    models.ChangesetAction.objects.create(
        changeset=changeset,
        type=models.ChangesetAction.TYPE_DELETED,
        timestamp=timezone.now()
    )

    event_handlers.on_changeset_soft_deleted(changeset, request)

    return changeset


def update_changeset_yaml(yaml_obj, f, commit):
    """Updates existing changeset from YAML document."""

    log.debug(yaml_obj)
    repo_filename = f['filename']
    blob_url = f['blob_url']

    committer_user = None
    if 'committer' in commit and 'login' in commit['committer']:
        user_qs = users_models.User.objects.filter(
            github_login=commit['committer']['login'])
        if user_qs.exists():
            committer_user = user_qs[0]

    qs = models.Changeset.objects.filter(repo_filename=repo_filename)
    if not qs.exists():
        log.warn('Changeset does not exists.')
        return None
    changeset = qs[0]

    with transaction.commit_on_success():
        models.ChangesetDetail.objects.filter(changeset=changeset).delete()

        changeset_obj = yaml_obj['changeset']
        new_changeset_obj = {}
        for k, v in changeset_obj.iteritems():
            if (k in [
                    'database_schema', 'type', 'classification']):
                new_changeset_obj[k] = v
            else:
                log.warn(u'Ignored changeset field %s.' % (k,))
        changeset_obj = new_changeset_obj
        changeset_obj['database_schema'] = (
            schemaversions_models.DatabaseSchema.objects.get(
                name=changeset_obj['database_schema']))
        changeset_obj['version_control_url'] = blob_url
        log.debug(pprint.pformat(changeset_obj))
        for k, v in changeset_obj.iteritems():
            setattr(changeset, k, v)
        changeset.review_status = models.Changeset.REVIEW_STATUS_NEEDS
        changeset.save()

        for changeset_detail_obj in yaml_obj['changeset_details']:
            changeset_detail_obj['changeset'] = changeset
            new_changeset_detail_obj = {}
            for k, v in changeset_detail_obj.iteritems():
                if (k in
                        [
                            'description', 'apply_sql', 'revert_sql',
                            'apply_verification_sql',
                            'revert_verification_sql',
                            'changeset']):
                    new_changeset_detail_obj[k] = v
                else:
                    log.warn(u'Ignored changeset detail field %s.' % (k,))
            changeset_detail_obj = new_changeset_detail_obj
            log.debug(pprint.pformat(changeset_detail_obj))
            models.ChangesetDetail.objects.create(**changeset_detail_obj)

        models.ChangesetAction.objects.create(
            changeset=changeset,
            type=models.ChangesetAction.TYPE_CHANGED_WITH_DATA_FROM_GITHUB_REPO,
            timestamp=timezone.now())

    event_handlers.on_changeset_updated(changeset)
    log.debug('changeset = %s' % (changeset,))
    return changeset


def save_changeset_yaml(yaml_obj, f, commit):
    """Saves changeset from YAML document."""

    log.debug(yaml_obj)
    repo_filename = f['filename']
    blob_url = f['blob_url']

    committer_user = None
    if 'committer' in commit and 'login' in commit['committer']:
        user_qs = users_models.User.objects.filter(
            github_login=commit['committer']['login'])
        if user_qs.exists():
            committer_user = user_qs[0]

    if models.Changeset.objects.filter(repo_filename=repo_filename).exists():
        log.warn('Changeset is already existing.')
        return

    with transaction.commit_on_success():
        changeset_obj = yaml_obj['changeset']
        new_changeset_obj = {}
        for k, v in changeset_obj.iteritems():
            if (
                    k in [
                        'database_schema', 'type', 'classification',
                        'submitted_by']):
                new_changeset_obj[k] = v
            else:
                log.warn(u'Ignored changeset field %s.' % (k,))
        changeset_obj = new_changeset_obj
        changeset_obj['database_schema'] = (
            schemaversions_models.DatabaseSchema.objects.get(
                name=changeset_obj['database_schema']))
        if committer_user:
            changeset_obj['submitted_by'] = committer_user
            log.debug('Using committer for submitted_by value.')
        else:
            changeset_obj['submitted_by'] = users_models.User.objects.get(
                name=changeset_obj['submitted_by'])
        changeset_obj['submitted_at'] = timezone.now()
        changeset_obj['repo_filename'] = repo_filename
        changeset_obj['version_control_url'] = blob_url
        log.debug(pprint.pformat(changeset_obj))
        changeset = models.Changeset.objects.create(**changeset_obj)

        for changeset_detail_obj in yaml_obj['changeset_details']:
            changeset_detail_obj['changeset'] = changeset
            new_changeset_detail_obj = {}
            for k, v in changeset_detail_obj.iteritems():
                if (k in
                        [
                            'description', 'apply_sql', 'revert_sql',
                            'apply_verification_sql',
                            'revert_verification_sql',
                            'changeset']):
                    new_changeset_detail_obj[k] = v
                else:
                    log.warn(u'Ignored changeset detail field %s.' % (k,))
            changeset_detail_obj = new_changeset_detail_obj
            log.debug(pprint.pformat(changeset_detail_obj))
            models.ChangesetDetail.objects.create(**changeset_detail_obj)

        models.ChangesetAction.objects.create(
            changeset=changeset,
            type=models.ChangesetAction.TYPE_CREATED_WITH_DATA_FROM_GITHUB_REPO,
            timestamp=timezone.now())

    event_handlers.on_changeset_submit(changeset)

    return changeset