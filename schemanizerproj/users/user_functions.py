import logging
from django.contrib.auth.models import User as AuthUser
from utils import helpers
from . import models

log = logging.getLogger(__name__)


def add_user(name, email, role, password, github_login=None):
    """Creates user."""
    role = helpers.get_model_instance(role, models.Role)

    auth_user = AuthUser.objects.create_user(name, email, password)
    schemanizer_user = models.User.objects.create(
        name=name, email=email, role=role, auth_user=auth_user,
        github_login=github_login)
    return schemanizer_user


def update_user(pk, name, email, role, github_login=None):
    """Updates user."""
    role = helpers.get_model_instance(role, models.Role)

    schemanizer_user = models.User.objects.get(pk=pk)
    schemanizer_user.name = name
    schemanizer_user.email = email
    schemanizer_user.role = role
    schemanizer_user.github_login = github_login
    schemanizer_user.save()
    auth_user = schemanizer_user.auth_user
    auth_user.username = schemanizer_user.name
    auth_user.email = schemanizer_user.email
    auth_user.save()

    return schemanizer_user
