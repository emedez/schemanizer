from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized

from schemanizer.logic import privileges as logic_privileges

MSG_UNAUTHORIZED = 'You are not allowed to access that resource.'


class EnvironmentAuthorization(ReadOnlyAuthorization):
    def create_list(self, object_list, bundle):
        if (
                logic_privileges.UserPrivileges(
                    bundle.request.user.schemanizer_user)
                .can_update_environment()):
            return object_list
        else:
            return []

    def create_detail(self, object_list, bundle):
        if (
                logic_privileges.UserPrivileges(
                    bundle.request.user.schemanizer_user)
                .can_update_environment()):
            return True
        else:
            raise Unauthorized(MSG_UNAUTHORIZED)

    def update_list(self, object_list, bundle):
        if (
                logic_privileges.UserPrivileges(
                    bundle.request.user.schemanizer_user)
                .can_update_environment()):
            return object_list
        else:
            return []

    def update_detail(self, object_list, bundle):
        if (
                logic_privileges.UserPrivileges(
                    bundle.request.user.schemanizer_user)
                .can_update_environment()):
            return True
        else:
            raise Unauthorized(MSG_UNAUTHORIZED)

    def delete_list(self, object_list, bundle):
        if (
                logic_privileges.UserPrivileges(
                    bundle.request.user.schemanizer_user)
                .can_delete_environment()
                ):
            return object_list
        else:
            return []

    def delete_detail(self, object_list, bundle):
        if (
                logic_privileges.UserPrivileges(
                    bundle.request.user.schemanizer_user)
                .can_delete_environment()
                ):
            return True
        else:
            raise Unauthorized(MSG_UNAUTHORIZED)

