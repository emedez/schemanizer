from tastypie.authorization import ReadOnlyAuthorization
from tastypie.exceptions import Unauthorized

from schemanizer import businesslogic

MSG_UNAUTHORIZED = 'You are not allowed to access that resource.'


class EnvironmentAuthorization(ReadOnlyAuthorization):
    def create_list(self, object_list, bundle):
        user = bundle.request.user.schemanizer_user
        if businesslogic.UserPrivileges.can_update_environments(user):
            return object_list
        else:
            return []

    def create_detail(self, object_list, bundle):
        user = bundle.request.user.schemanizer_user
        if businesslogic.UserPrivileges.can_update_environments(user):
            return True
        else:
            raise Unauthorized(MSG_UNAUTHORIZED)

    def update_list(self, object_list, bundle):
        user = bundle.request.user.schemanizer_user
        if businesslogic.UserPrivileges.can_update_environments(user):
            return object_list
        else:
            return []

    def update_detail(self, object_list, bundle):
        user = bundle.request.user.schemanizer_user
        if businesslogic.UserPrivileges.can_update_environments(user):
            return True
        else:
            raise Unauthorized(MSG_UNAUTHORIZED)

    def delete_list(self, object_list, bundle):
        user = bundle.request.user.schemanizer_user
        if businesslogic.UserPrivileges.can_delete_environments(user):
            return object_list
        else:
            return []

    def delete_detail(self, object_list, bundle):
        user = bundle.request.user.schemanizer_user
        if businesslogic.UserPrivileges.can_delete_environments(user):
            return True
        else:
            raise Unauthorized(MSG_UNAUTHORIZED)

