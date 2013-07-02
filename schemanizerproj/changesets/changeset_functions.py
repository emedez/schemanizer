import logging
from django.db import transaction
from django.utils import timezone
from changesets.models import Changeset, ChangesetAction
from schemanizer.logic.changeset_logic import log
from users.models import User
from utils import exceptions
from . import event_handlers, models
from schemanizer.logic import privileges_logic
from utils.helpers import get_model_instance

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

    ChangesetAction.objects.create(
        changeset=changeset,
        type=ChangesetAction.TYPE_DELETED,
        timestamp=timezone.now()
    )

    event_handlers.on_changeset_soft_deleted(changeset, request)

    return changeset