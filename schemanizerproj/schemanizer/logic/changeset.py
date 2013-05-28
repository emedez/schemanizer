"""General changeset logic."""
import logging

from django.db import transaction
from django.utils import timezone

from schemanizer import exceptions, models, utils
from schemanizer.logic import (
    mail as logic_mail,
    privileges as logic_privileges)

log = logging.getLogger(__name__)


def soft_delete_changeset(changeset, user):
    """Soft deletes changeset."""

    changeset = utils.get_model_instance(changeset, models.Changeset)
    user = utils.get_model_instance(user, models.User)

    logic_privileges.UserPrivileges(user).check_soft_delete_changeset(changeset)

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


def changeset_submit_from_form(**kwargs):
    """Submits changeset.

    expected keyword arguments:
        changeset_form
        changeset_detail_formset
        user
            - this is used as value for submitted_by
    """
    now = timezone.now()

    changeset_form = kwargs.get('changeset_form')
    changeset_detail_formset = kwargs.get('changeset_detail_formset')
    submitted_by = kwargs.get('user')
    submitted_at = now

    changeset = changeset_form.save(commit=False)
    changeset.submitted_by = submitted_by
    changeset.submitted_at = submitted_at
    changeset.save()
    changeset_form.save_m2m()
    changeset_detail_formset.save()

    models.ChangesetAction.objects.create(
        changeset=changeset,
        type=models.ChangesetAction.TYPE_CREATED,
        timestamp=now)

    log.info('Changeset [id=%s] was submitted.' % (changeset.id,))
    logic_mail.send_changeset_submitted_mail(changeset)

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

    logic_mail.send_changeset_submitted_mail(changeset)
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
    if logic_privileges.UserPrivileges(user).can_update_changeset(changeset):
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

        logic_mail.send_changeset_updated_mail(changeset)

    else:
        raise exceptions.PrivilegeError(
            u'User is not allowed to update changeset.')

    return changeset


def changeset_update(changeset, changeset_details, to_be_deleted_changeset_details, user):
    user = utils.get_model_instance(user, models.User)

    if logic_privileges.UserPrivileges(user).can_update_changeset(changeset):
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

        logic_mail.send_changeset_updated_mail(changeset)

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

    if logic_privileges.UserPrivileges(user).can_approve_changeset(changeset):
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

        logic_mail.send_changeset_approved_mail(changeset)

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

    if logic_privileges.UserPrivileges(user).can_reject_changeset(changeset):
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

        logic_mail.send_changeset_rejected_mail(changeset)

        return changeset

    else:
        log.debug(u'changeset:\n%s\n\nuser=%s' % (changeset, user.name))
        raise exceptions.PrivilegeError(
            u'User is not allowed to reject changeset.')
