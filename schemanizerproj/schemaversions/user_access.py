import logging
from django.core.urlresolvers import resolve
from users import models as users_models
from utils import exceptions

log = logging.getLogger(__name__)

MSG_ACCESS_DENIED = 'Access denied.'


def check_database_schema_list_access(request, *args, **kwargs):
    role_class = users_models.Role
    if request.user.schemanizer_user.role.name not in (
            role_class.NAME.developer, role_class.NAME.dba,
            role_class.NAME.admin):
        raise exceptions.UserAccessError(MSG_ACCESS_DENIED)


def check_schema_version_list_access(request, *args, **kwargs):
    role_class = users_models.Role
    if request.user.schemanizer_user.role.name not in (
            role_class.NAME.developer, role_class.NAME.dba,
            role_class.NAME.admin):
        raise exceptions.UserAccessError(MSG_ACCESS_DENIED)


def check_schema_version_generate_access(request, *args, **kwargs):
    role_class = users_models.Role
    if request.user.schemanizer_user.role.name not in (
            role_class.NAME.developer, role_class.NAME.dba,
            role_class.NAME.admin):
        raise exceptions.UserAccessError(MSG_ACCESS_DENIED)


access_map = {
    'schemaversions_database_schema_list': check_database_schema_list_access,
    'schemaversions_schema_version_list': check_schema_version_list_access,
    'schemaversions_schema_version_generate': check_schema_version_generate_access,
}


def check_access(request, *args, **kwargs):
    user_privileges = None
    url_name = resolve(request.path_info).url_name
    if url_name in access_map:
        user_privileges = access_map[url_name](request, *args, **kwargs)
    return user_privileges
