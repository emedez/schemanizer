import logging
from django.contrib import messages
from . import exceptions

log = logging.getLogger(__name__)


def check_access(check_access_func=None):
    """View dispatch decorator that checks user access and updates view.

    Args:

        check_access_func - the actual function that will perform the access
            check. It should have the following signature:

            check_access_func(request, *args, **kwargs)
    """
    def inner_decorator(fn):
        """Actual decorator.

        Args:

            fn - dispatch function to decorate. Signature should be:

                fn(request, *args, **kwargs)
        """
        def inner_method(self, request, *args, **kwargs):
            self.allow_user_access = False
            self.user_privileges = None
            try:
                if check_access_func:
                    self.user_privileges = check_access_func(request)
                self.allow_user_access = True
            except Exception, e:
                error_message = 'ERROR %s: %s' % (type(e), e)
                log.exception(error_message)
                messages.error(self.request, error_message)

            return fn(self, request, *args, **kwargs)
        return inner_method
    return inner_decorator