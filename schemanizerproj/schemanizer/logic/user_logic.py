"""User-related logic."""

import logging

from django.db import transaction

from schemanizer.logic import privileges_logic
from users.models import User
from utils.helpers import get_model_instance

log = logging.getLogger(__name__)








def delete_user(user, to_be_del_user):
    """Deletes user."""
    user = get_model_instance(user, User)
    to_be_del_user = get_model_instance(to_be_del_user, User)

    privileges_logic.UserPrivileges(user).check_delete_user()

    with transaction.commit_on_success():
        to_be_del_user_id = to_be_del_user.id
        auth_user = to_be_del_user.auth_user
        to_be_del_user.delete()
        auth_user.delete()

    log.debug(u'User was deleted, id=%s.' % (to_be_del_user_id,))