import logging
from django.core.urlresolvers import resolve
from users import models as users_models
from utils import exceptions

log = logging.getLogger(__name__)

MSG_ACCESS_DENIED = 'Access denied.'


def get_environment_list_user_privileges(request, *args, **kwargs):
    role_class = users_models.Role
    can_add = can_update = can_delete = (
        request.user.schemanizer_user.role.name in [
            role_class.NAME.dba, role_class.NAME.admin])
    return dict(
        can_add=can_add, can_update=can_update, can_delete=can_delete)


def check_environment_list_access(request, *args, **kwargs):
    role_class = users_models.Role
    if request.user.schemanizer_user.role.name not in (
            role_class.NAME.developer, role_class.NAME.dba,
            role_class.NAME.admin):
        raise exceptions.UserAccessError(MSG_ACCESS_DENIED)
    return get_environment_list_user_privileges(request, *args, **kwargs)


def check_server_list_access(request, *args, **kwargs):
    role_class = users_models.Role
    if request.user.schemanizer_user.role.name not in (
            role_class.NAME.developer, role_class.NAME.dba,
            role_class.NAME.admin):
        raise exceptions.UserAccessError(MSG_ACCESS_DENIED)


access_map = {
    'servers_environment_list': check_environment_list_access,
    'servers_server_list': check_server_list_access,
}


def check_access(request, *args, **kwargs):
    user_privileges = None
    url_name = resolve(request.path_info).url_name
    if url_name in access_map:
        user_privileges = access_map[url_name](request, *args, **kwargs)
    return user_privileges
