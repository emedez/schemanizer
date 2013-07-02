"""General changeset logic."""
import logging
import pprint

from django.db import transaction
from django.utils import timezone
from changesets.event_handlers import on_changeset_submit
from changesets.models import Changeset, ChangesetDetail, ChangesetAction
from emails.email_functions import send_mail_changeset_submitted, send_mail_changeset_updated

from schemanizer.logic import privileges_logic
from schemaversions.models import DatabaseSchema
from users.models import User
from utils.exceptions import PrivilegeError
from utils.helpers import get_model_instance

log = logging.getLogger(__name__)





def delete_changeset(changeset):
    """Deletes changeset."""

    changeset = get_model_instance(changeset, Changeset)

    changeset_id = changeset.id
    changeset.delete()
    log.info('Changeset [id=%s] was deleted.' % (changeset_id,))











def update_changeset_yaml(yaml_obj, f, commit):
    """Updates existing changeset from YAML document."""

    log.debug(yaml_obj)
    repo_filename = f['filename']
    blob_url = f['blob_url']

    committer_user = None
    if 'committer' in commit and 'login' in commit['committer']:
        user_qs = User.objects.filter(
            github_login=commit['committer']['login'])
        if user_qs.exists():
            committer_user = user_qs[0]

    qs = Changeset.objects.filter(repo_filename=repo_filename)
    if not qs.exists():
        log.warn('Changeset does not exists.')
        return None
    changeset = qs[0]

    with transaction.commit_on_success():
        ChangesetDetail.objects.filter(changeset=changeset).delete()

        changeset_obj = yaml_obj['changeset']
        new_changeset_obj = {}
        for k, v in changeset_obj.iteritems():
            if (k in [
                    'database_schema', 'type', 'classification']):
                new_changeset_obj[k] = v
            else:
                log.warn(u'Ignored changeset field %s.' % (k,))
        changeset_obj = new_changeset_obj
        changeset_obj['database_schema'] = DatabaseSchema.objects.get(
            name=changeset_obj['database_schema'])
        changeset_obj['version_control_url'] = blob_url
        log.debug(pprint.pformat(changeset_obj))
        for k, v in changeset_obj.iteritems():
            setattr(changeset, k, v)
        changeset.review_status = Changeset.REVIEW_STATUS_NEEDS
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
            ChangesetDetail.objects.create(**changeset_detail_obj)

        ChangesetAction.objects.create(
            changeset=changeset,
            type=ChangesetAction.TYPE_CHANGED_WITH_DATA_FROM_GITHUB_REPO,
            timestamp=timezone.now())

    send_mail_changeset_updated(changeset)
    log.debug('changeset = %s' % (changeset,))
    return changeset


def save_changeset_yaml(yaml_obj, f, commit):
    """Saves changeset from YAML document."""

    log.debug(yaml_obj)
    repo_filename = f['filename']
    blob_url = f['blob_url']

    committer_user = None
    if 'committer' in commit and 'login' in commit['committer']:
        user_qs = User.objects.filter(
            github_login=commit['committer']['login'])
        if user_qs.exists():
            committer_user = user_qs[0]

    if Changeset.objects.filter(repo_filename=repo_filename).exists():
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
        changeset_obj['database_schema'] = DatabaseSchema.objects.get(
            name=changeset_obj['database_schema'])
        if committer_user:
            changeset_obj['submitted_by'] = committer_user
        else:
            changeset_obj['submitted_by'] = User.objects.get(
                name=changeset_obj['submitted_by'])
        changeset_obj['submitted_at'] = timezone.now()
        changeset_obj['repo_filename'] = repo_filename
        changeset_obj['version_control_url'] = blob_url
        log.debug(pprint.pformat(changeset_obj))
        changeset = Changeset.objects.create(**changeset_obj)

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
            ChangesetDetail.objects.create(**changeset_detail_obj)

        ChangesetAction.objects.create(
            changeset=changeset,
            type=ChangesetAction.TYPE_CREATED_WITH_DATA_FROM_GITHUB_REPO,
            timestamp=timezone.now())

    on_changeset_submit(changeset)

    return changeset


def changeset_submit(changeset, changeset_details, user):
    user = get_model_instance(user, User)

    if changeset.pk:
        raise Exception('Only new changesets can be submitted.')

    for changeset_detail in changeset_details:
        if changeset_detail.pk:
            raise Exception(
                'Only new changeset detail is allowed for changeset '
                'submission.')

    now = timezone.now()

    with transaction.commit_on_success():
        changeset.submitted_by = user
        changeset.submitted_at = now
        changeset.save()

        for changeset_detail in changeset_details:
            changeset_detail.changeset = changeset
            changeset_detail.save()

        ChangesetAction.objects.create(
            changeset=changeset,
            type=ChangesetAction.TYPE_CREATED,
            timestamp=now
        )

    send_mail_changeset_submitted(changeset)
    log.info('Changeset [id=%s] was submitted.' % (changeset.id,))

    return changeset





def changeset_update(changeset, changeset_details, to_be_deleted_changeset_details, user):
    user = get_model_instance(user, User)

    if privileges_logic.UserPrivileges(user).can_update_changeset(changeset):
        with transaction.commit_on_success():
            now = timezone.now()

            for tbdc in to_be_deleted_changeset_details:
                if tbdc.pk and tbdc.changeset and tbdc.changeset.id == changeset.id:
                    tbdc.delete()
                else:
                    raise Exception('to_be_deleted_changeset_details contain and invalid changeset detail.')

            changeset.review_status = changeset.REVIEW_STATUS_NEEDS
            changeset.save()

            for cd in changeset_details:
                if cd.pk:
                    if cd.changeset.id == changeset.id:
                        cd.save()
                    else:
                        raise Exception('One of the changeset details have invalid changeset value.')
                else:
                    cd.changeset = changeset
                    cd.save()

            # Create entry on changeset actions
            ChangesetAction.objects.create(
                changeset=changeset,
                type=ChangesetAction.TYPE_CHANGED,
                timestamp=now)

        log.info(u'Changeset [id=%s] was updated.' % (changeset.id,))

        send_mail_changeset_updated(changeset)

        return changeset
    else:
        raise PrivilegeError(
            'User is not allowed to update changeset.')







