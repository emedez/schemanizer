import logging
import threading

from django.conf import settings
from changesetapplies.models import ChangesetApply
from changesets.models import Changeset

from schemanizer.logic import privileges_logic
from servers.models import Server
from users.models import User
from utils.exceptions import PrivilegeError
from utils.helpers import get_model_instance

log = logging.getLogger(__name__)


class ChangesetApplyThread(threading.Thread):
    def __init__(self, changeset, user, server, connection_options,):
        super(ChangesetApplyThread, self).__init__()
        self.daemon = True

        self.changeset = get_model_instance(changeset, Changeset)
        self.user = get_model_instance(user, User)
        self.server = get_model_instance(server, Server)
        self.connection_options = connection_options

        self.messages = []

        self.has_errors = False
        self.changeset_detail_applies = []
        self.changeset_detail_apply_ids = []

    def _store_message(self, message, message_type='info', extra=None):
        """Stores message."""
        self.messages.append(dict(
            message=message, message_type=message_type, extra=extra))

    def _message_callback(self, obj, message, message_type, extra=None):
        """Message callback.

        This is provided to allow thread to take a look at the messages
        even when the ChangesetApply logic run has not yet completed.
        """
        self._store_message(message, message_type, extra)

    def run(self):
        msg = 'Changeset apply thread started.'
        log.info(msg)
        self._store_message(msg)

        try:
            changeset_apply = ChangesetApply(
                self.changeset, self.user, self.server,
                self.connection_options,
                self._message_callback)
            changeset_apply.run()

            self.messages = []
            self._store_message(msg)
            self.messages.extend(changeset_apply.messages)
            self.has_errors = changeset_apply.has_errors
            self.changeset_detail_applies = (
                changeset_apply.changeset_detail_applies)
            self.changeset_detail_apply_ids = (
                changeset_apply.changeset_detail_apply_ids)

        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            log.exception(msg)
            self._store_message(msg, 'error')
            self.has_errors = True

        finally:
            msg = 'Changeset apply thread ended.'
            log.info(msg)
            self._store_message(msg)


def start_changeset_apply_thread(changeset, user, server):
    changeset = get_model_instance(changeset, Changeset)
    user = get_model_instance(user, User)
    server = get_model_instance(server, Server)

    if not privileges_logic.can_user_apply_changeset(user, changeset):
        raise PrivilegeError(
            'User is not allowed to apply changeset.')

    connection_options = {}
    if settings.AWS_MYSQL_USER:
        connection_options['user'] = settings.AWS_MYSQL_USER
    if settings.AWS_MYSQL_PASSWORD:
        connection_options['passwd'] = settings.AWS_MYSQL_PASSWORD

    thread = ChangesetApplyThread(changeset, user, server, connection_options)
    thread.start()
    return thread


