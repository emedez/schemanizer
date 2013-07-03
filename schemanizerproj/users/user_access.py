import logging
from django.core.urlresolvers import resolve
from users import models as users_models
from utils import exceptions

log = logging.getLogger(__name__)

MSG_ACCESS_DENIED = 'Access denied.'


def check_admin_only_access(request, *args, **kwargs):
    role_class = users_models.Role
    if request.user.schemanizer_user.role.name not in [role_class.NAME.admin]:
        raise exceptions.UserAccessError(MSG_ACCESS_DENIED)


access_map = {
    'users_user_list': check_admin_only_access,
    'users_user_add': check_admin_only_access,
    'users_user_update': check_admin_only_access,
    'users_user_delete': check_admin_only_access,
}


def check_access(request, *args, **kwargs):
    user_privileges = None
    url_name = resolve(request.path_info).url_name
    if url_name in access_map:
        user_privileges = access_map[url_name](request, *args, **kwargs)
    return user_privileges
