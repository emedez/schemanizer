"""User-related logic."""

import logging

from django.contrib.auth.models import User as AuthUser
from django.db import transaction

from schemanizer import exceptions, models, utils
from schemanizer.logic import privileges_logic

log = logging.getLogger(__name__)


def create_user(user, name, email, role, password, github_login=None):
    """Creates user."""
    user = utils.get_model_instance(user, models.User)
    role = utils.get_model_instance(role, models.Role)

    privileges_logic.UserPrivileges(user).check_create_user()

    with transaction.commit_on_success():
        auth_user = AuthUser.objects.create_user(name, email, password)
        schemanizer_user = models.User.objects.create(
            name=name, email=email, role=role, auth_user=auth_user,
            github_login=github_login)

    log.debug(u'User was created, id=%s.' % (schemanizer_user.id,))

    return schemanizer_user


def update_user(user, id, name, email, role, github_login=None):
    """Updates user."""
    user = utils.get_model_instance(user, models.User)
    role = utils.get_model_instance(role, models.Role)

    privileges_logic.UserPrivileges(user).check_update_user()

    with transaction.commit_on_success():
        schemanizer_user = models.User.objects.get(id=id)
        schemanizer_user.name = name
        schemanizer_user.email = email
        schemanizer_user.role = role
        schemanizer_user.github_login = github_login
        schemanizer_user.save()
        auth_user = schemanizer_user.auth_user
        auth_user.username = schemanizer_user.name
        auth_user.email = schemanizer_user.email
        auth_user.save()

    log.debug(u'User was updated, id=%s.' % (id,))

    return schemanizer_user


def delete_user(user, to_be_del_user):
    """Deletes user."""
    user = utils.get_model_instance(user, models.User)
    to_be_del_user = utils.get_model_instance(to_be_del_user, models.User)

    privileges_logic.UserPrivileges(user).check_delete_user()

    with transaction.commit_on_success():
        to_be_del_user_id = to_be_del_user.id
        auth_user = to_be_del_user.auth_user
        to_be_del_user.delete()
        auth_user.delete()

    log.debug(u'User was deleted, id=%s.' % (to_be_del_user_id,))