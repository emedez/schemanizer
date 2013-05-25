"""User privileges."""

import logging

from schemanizer import exceptions, models, utils

MSG_CREATE_USER_NOT_ALLOWED = 'Creating user is not allowed.'
MSG_DELETE_USER_NOT_ALLOWED = 'Deleting user is not allowed.'
MSG_SAVE_SCHEMA_DUMP_NOT_ALLOWED = 'Save schema dump is not allowed.'
MSG_SOFT_DELETE_CHANGESET_NOT_ALLOWED = 'Soft delete changeset is not allowed.'
MSG_UPDATE_USER_NOT_ALLOWED = 'Updating user is not allowed.'

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


class UserPrivileges(object):
    """User privileges."""

    def __init__(self, user):
        """Initializes instance."""
        self._user = utils.get_model_instance(user, models.User)

    @property
    def user(self):
        """Returns user."""
        return self._user

    def can_create_user(self):
        """Checks if user can create users."""
        if self._user.role.name in [models.Role.ROLE_ADMIN]:
            return True
        else:
            return False

    def check_create_user(self):
        """Raises PrivilegeError if can_create_user() returns False."""
        if not self.can_create_user():
            raise exceptions.PrivilegeError(MSG_CREATE_USER_NOT_ALLOWED)

    def can_update_user(self):
        """Checks if user can update users."""
        if self._user.role.name in [models.Role.ROLE_ADMIN]:
            return True
        else:
            return False

    def check_update_user(self):
        """Raises PrivilegeError if can_update_user() returns False."""
        if not self.can_update_user():
            raise exceptions.PrivilegeError(MSG_UPDATE_USER_NOT_ALLOWED)

    def can_delete_user(self):
        """Checks if user can delete users."""
        if self._user.role.name in [models.Role.ROLE_ADMIN]:
            return True
        else:
            return False

    def check_delete_user(self):
        """Raises PrivilegeError if can_delete_user() returns False."""
        if not self.can_delete_user():
            raise exceptions.PrivilegeError(MSG_DELETE_USER_NOT_ALLOWED)

    def can_update_environment(self):
        """Checks if user can update environments."""
        if self._user.role.name in [
                models.Role.ROLE_DBA, models.Role.ROLE_ADMIN]:
            return True
        else:
            return False

    def can_delete_environment(self):
        """Checks if user can delete environments."""
        if (
                self._user.role.name in [
                    models.Role.ROLE_DBA, models.Role.ROLE_ADMIN]
                ):
            return True
        else:
            return False

    def can_save_schema_dump(self):
        """Checks if user can save schema dumps."""
        # Everyone can save schema dumps.
        return True

    def check_save_schema_dump(self):
        """Raises PrivilegeError if can_save_schema_dump() returns False."""
        if not self.can_save_schema_dump():
            raise exceptions.PrivilegeError(MSG_SAVE_SCHEMA_DUMP_NOT_ALLOWED)

    def can_soft_delete_changeset(self, changeset):
        """Checks if user can soft delete changeset."""

        changeset = utils.get_model_instance(changeset, models.Changeset)

        if not changeset.pk:
            # Cannot soft delete unsaved changeset.
            return False

        if changeset.is_deleted:
            # Cannot soft delete that was already soft deleted.
            return False

        if (
                self._user.role.name in [
                    models.Role.ROLE_DBA, models.Role.ROLE_ADMIN]
                ):
            # dbas and admins can soft delete changeset
            return True

        if (
                self._user.role.name in [models.Role.ROLE_DEVELOPER] and
                changeset.review_status != models.Changeset.REVIEW_STATUS_APPROVED
                ):
            # developers can only soft delete changesets that were not yet approved
            return True

        return False

    def check_soft_delete_changeset(self, changeset):
        """Raises PrivilegeError if can_soft_delete_changeset() returns False."""
        if not self.can_soft_delete_changeset(changeset):
            raise exceptions.PrivilegeError(
                MSG_SOFT_DELETE_CHANGESET_NOT_ALLOWED)

    def can_update_changeset(self, changeset):
        """Checks if user can update changeset."""

        changeset = utils.get_model_instance(changeset, models.Changeset)

        if not changeset.pk:
            # Cannot update unsaved changesets.
            return False

        if self._user.role.name in [models.Role.ROLE_DBA, models.Role.ROLE_ADMIN]:
            # dbas and admins can always update changeset.
            return True

        if self._user.role.name in [models.Role.ROLE_DEVELOPER]:
            # developers can update changesets only if it was not yet approved.
            if changeset.review_status != models.Changeset.REVIEW_STATUS_APPROVED:
                return True

        return False

    def can_approve_changeset(self, changeset):
        """Checks if user can approve changeset."""

        changeset = utils.get_model_instance(changeset, models.Changeset)

        if not changeset.pk:
            # Cannot approve unsaved changeset.
            return False

        if changeset.review_status == models.Changeset.REVIEW_STATUS_APPROVED:
            # cannot approve, it is already approved
            return False

        if self._user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
            if changeset.review_status in (models.Changeset.REVIEW_STATUS_IN_PROGRESS):
                return True
        else:
            return False

    def can_reject_changeset(self, changeset):
        """Checks if user can reject changeset."""

        if type(changeset) in (int, long):
            changeset = models.Changeset.objects.get(pk=changeset)

        if not changeset.pk:
            # Cannot reject unsaved changeset.
            return False

        if changeset.review_status == models.Changeset.REVIEW_STATUS_REJECTED:
            # cannot reject, it is already rejected
            return False

        if self._user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
            # allow reject regardless of review status
            return True
        else:
            return False
