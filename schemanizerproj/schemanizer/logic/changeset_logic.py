"""General changeset logic."""
import logging
import pprint

from django.db import transaction
from django.utils import timezone

from schemanizer import exceptions, models, utils
from schemanizer.logic import mail_logic
from schemanizer.logic import privileges_logic

log = logging.getLogger(__name__)


def soft_delete_changeset(changeset, user):
    """Soft deletes changeset."""

    changeset = utils.get_model_instance(changeset, models.Changeset)
    user = utils.get_model_instance(user, models.User)

    privileges_logic.UserPrivileges(user).check_soft_delete_changeset(
        changeset)

    with transaction.commit_on_success():
        changeset.is_deleted = 1
        changeset.save()

        models.ChangesetAction.objects.create(
            changeset=changeset,
            type=models.ChangesetAction.TYPE_DELETED,
            timestamp=timezone.now()
        )

    log.info('Changeset [id=%s] was soft deleted.' % (changeset.id,))

    return changeset


def delete_changeset(changeset):
    """Deletes changeset."""

    changeset = utils.get_model_instance(changeset, models.Changeset)

    changeset_id = changeset.id
    changeset.delete()
    log.info('Changeset [id=%s] was deleted.' % (changeset_id,))


def changeset_submit_from_form(send_mail=True, **kwargs):
    """Submits changeset.

    expected keyword arguments:
        changeset_form
        changeset_detail_formset
        user
            - this is used as value for submitted_by
    """

    changeset_form = kwargs.get('changeset_form')
    changeset_detail_formset = kwargs.get('changeset_detail_formset')
    submitted_by = kwargs.get('user')
    submitted_at = timezone.now()

    changeset = changeset_form.save(commit=False)
    changeset.submitted_by = submitted_by
    changeset.submitted_at = submitted_at
    changeset.save()
    changeset_form.save_m2m()
    changeset_detail_formset.save()

    models.ChangesetAction.objects.create(
        changeset=changeset,
        type=models.ChangesetAction.TYPE_CREATED,
        timestamp=timezone.now())

    log.info('Changeset [id=%s] was submitted.' % (changeset.id,))
    if send_mail:
        mail_logic.send_changeset_submitted_mail(changeset)

    return changeset


def process_changeset_form_submission(**kwargs):
    """Saves submitted changeset.

    Arguments:

        changeset_form: an instance of schemanizer.forms.ChangesetForm

        changeset_detail_formset: formset of
            schemanizer.forms.ChangesetDetailForm

        user: value for Changeset's submitted_by field

    Returns:

        Saved changeset
    """

    kwargs.update({'send_mail': False})
    with transaction.commit_on_success():
        changeset = changeset_submit_from_form(**kwargs)
    on_changeset_submit(changeset)
    return changeset


def on_changeset_submit(changeset):
    """Queues tasks for changeset submit event."""
    from schemanizer import tasks
    tasks.review_changeset.delay(changeset=changeset.pk)


def update_changeset_yaml(yaml_obj, repo_filename):
    """Updates existing changeset from YAML document."""

    log.debug(yaml_obj)

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
                    'database_schema', 'type', 'classification',
                    'version_control_url']):
                new_changeset_obj[k] = v
            else:
                log.warn(u'Ignored changeset field %s.' % (k,))
        changeset_obj = new_changeset_obj
        changeset_obj['database_schema'] = models.DatabaseSchema.objects.get(
            name=changeset_obj['database_schema'])
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
            type=models.ChangesetAction.TYPE_CHANGED,
            timestamp=timezone.now())

    mail_logic.send_changeset_updated_mail(changeset)
    log.debug('changeset = %s' % (changeset,))
    return changeset


def save_changeset_yaml(yaml_obj, repo_filename):
    """Saves changeset from YAML document."""

    log.debug(yaml_obj)

    if models.Changeset.objects.filter(repo_filename=repo_filename).exists():
        #msg = (u'Changeset with repo_filename=%s already exists.' % (
        #    repo_filename,))
        #raise exceptions.Error(msg)
        log.warn('Changeset is already existing.')
        return

    with transaction.commit_on_success():
        changeset_obj = yaml_obj['changeset']
        new_changeset_obj = {}
        for k, v in changeset_obj.iteritems():
            if (
                    k in [
                        'database_schema', 'type', 'classification',
                        'version_control_url', 'submitted_by']):
                new_changeset_obj[k] = v
            else:
                log.warn(u'Ignored changeset field %s.' % (k,))
        changeset_obj = new_changeset_obj
        changeset_obj['database_schema'] = models.DatabaseSchema.objects.get(
            name=changeset_obj['database_schema'])
        changeset_obj['submitted_by'] = models.User.objects.get(
            name=changeset_obj['submitted_by'])
        changeset_obj['submitted_at'] = timezone.now()
        changeset_obj['repo_filename'] = repo_filename
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
            type=models.ChangesetAction.TYPE_CREATED,
            timestamp=timezone.now())

    on_changeset_submit(changeset)

    return changeset


def changeset_submit(changeset, changeset_details, user):
    user = utils.get_model_instance(user, models.User)

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

        models.ChangesetAction.objects.create(
            changeset=changeset,
            type=models.ChangesetAction.TYPE_CREATED,
            timestamp=now
        )

    mail_logic.send_changeset_submitted_mail(changeset)
    log.info('Changeset [id=%s] was submitted.' % (changeset.id,))

    return changeset


def changeset_update_from_form(**kwargs):
    """Updates changeset.

    expected keyword arguments:
        changeset_form
        changeset_detail_formset
        user
    """
    changeset_form = kwargs.get('changeset_form')
    changeset_detail_formset = kwargs.get('changeset_detail_formset')
    user = kwargs.get('user')

    changeset = changeset_form.save(commit=False)
    if privileges_logic.UserPrivileges(user).can_update_changeset(changeset):
        with transaction.commit_on_success():
            #
            # Update changeset
            #
            now = timezone.now()
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
                timestamp=now)

        log.info(u'Changeset [id=%s] was updated.' % (changeset.id,))

        mail_logic.send_changeset_updated_mail(changeset)

    else:
        raise exceptions.PrivilegeError(
            u'User is not allowed to update changeset.')

    return changeset


def changeset_update(changeset, changeset_details, to_be_deleted_changeset_details, user):
    user = utils.get_model_instance(user, models.User)

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
            models.ChangesetAction.objects.create(
                changeset=changeset,
                type=models.ChangesetAction.TYPE_CHANGED,
                timestamp=now)

        log.info(u'Changeset [id=%s] was updated.' % (changeset.id,))

        mail_logic.send_changeset_updated_mail(changeset)

        return changeset
    else:
        raise exceptions.PrivilegeError(
            'User is not allowed to update changeset.')


def changeset_approve(changeset, user):
    """Approves changeset."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if privileges_logic.UserPrivileges(user).can_approve_changeset(changeset):
        now = timezone.now()
        with transaction.commit_on_success():
            #
            # Update changeset
            #
            changeset.review_status = models.Changeset.REVIEW_STATUS_APPROVED
            changeset.approved_by = user
            changeset.approved_at = now
            changeset.save()
            #
            # Create changeset action entry.
            models.ChangesetAction.objects.create(
                changeset=changeset,
                type=models.ChangesetAction.TYPE_APPROVED,
                timestamp=now)

        log.info(u'Changeset [id=%s] was approved.' % (changeset.id,))

        mail_logic.send_changeset_approved_mail(changeset)

        return changeset

    else:
        raise exceptions.PrivilegeError(
            u'User is not allowed to approve changeset.')


def changeset_reject(changeset, user):
    """Rejects changeset."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if privileges_logic.UserPrivileges(user).can_reject_changeset(changeset):
        now = timezone.now()
        with transaction.commit_on_success():
            #
            # Update changeset.
            #
            changeset.review_status = models.Changeset.REVIEW_STATUS_REJECTED
            changeset.approved_by = user
            changeset.approved_at = now
            changeset.save()
            #
            # Create changeset actions entry.
            models.ChangesetAction.objects.create(
                changeset=changeset,
                type=models.ChangesetAction.TYPE_REJECTED,
                timestamp=now)

        log.info(u'Changeset [id=%s] was rejected.' % (changeset.id,))

        mail_logic.send_changeset_rejected_mail(changeset)

        return changeset

    else:
        log.debug(u'changeset:\n%s\n\nuser=%s' % (changeset, user.name))
        raise exceptions.PrivilegeError(
            u'User is not allowed to reject changeset.')

