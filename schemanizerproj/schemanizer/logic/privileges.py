"""Privileges-related logic."""

import logging

from schemanizer import models, utils

log = logging.getLogger(__name__)


def can_user_review_changeset(user, changeset=None):
    """Checks if changeset review_status can be set to 'in_progress' by user.

    Only DBAs and admins can review changesets.

    Args:

        user: User ID or an instance of User.

        changeset: Changeset ID or an instance of Changeset.

    Returns:

        True if user can review changeset, otherwise False.
    """

    user = utils.get_model_instance(user, models.User)
    if changeset is not None:
        changeset = utils.get_model_instance(changeset, models.Changeset)

    # Only DBAs and admins can review changesets.
    if user.role.name not in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
        return False

    if changeset and not changeset.pk:
        # Reviews are only allowed on saved changesets.
        return False

    return True


def can_user_apply_changeset(user, changeset=None):
    user = utils.get_model_instance(user, models.User)
    if changeset is not None:
        changeset = utils.get_model_instance(changeset, models.Changeset)

    if changeset:
        if not changeset.pk:
            # Cannot apply unsaved changeset.
            return False

        # only approved changesets can be applied
        if changeset.review_status not in (
                models.Changeset.REVIEW_STATUS_APPROVED,):
            return False

        if (user.role.name in (models.Role.ROLE_DEVELOPER,) and
                changeset.classification in (
                    models.Changeset.CLASSIFICATION_LOWRISK,
                    models.Changeset.CLASSIFICATION_PAINLESS)):
            return True

    if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
        return True

    return False
