import logging
from django.utils import timezone

from schemanizer import models

log = logging.getLogger(__name__)

ROLE_ADMIN = u'admin'
ROLE_DBA = u'dba'
ROLE_DEVELOPER = u'developer'
ROLE_LIST_ALL = (ROLE_ADMIN, ROLE_DBA, ROLE_DEVELOPER)


def user_role_is_in_roles(user, role_name_list):
    """Returns True, if user's role is in the list, otherwise False."""
    schemanizer_user = user.schemanizer_user
    role = None
    if schemanizer_user:
        role = schemanizer_user.role
    if role and role.name in role_name_list:
        return True
    elif user.is_superuser and ROLE_ADMIN in role_name_list:
        return True
    else:
        return False


def changeset_submit(**kwargs):
    """Submits changeset.

    expected keyword arguments:
        type
        classification
        version_control_url
        changeset_form
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
        type=models.ChangesetAction.TYPE_NEW,
        timestamp = now)

    log.info('Changeset submitted:\n%s' % (changeset,))

    return changeset


def get_to_be_reviewed_changesets():
    """Returns changesets that needs to be reviewed."""
    return (
        models.Changeset.objects
        .filter(review_status=models.Changeset.REVIEW_STATUS_NEEDS))
