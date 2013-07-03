"""General changeset logic."""
import logging

from django.db import transaction
from django.utils import timezone
from changesets.models import Changeset, ChangesetAction
from emails.email_functions import send_mail_changeset_submitted, send_mail_changeset_updated

from schemanizer.logic import privileges_logic
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







