import logging
import threading

from changesetreviews.models import ChangesetReview
from changesets.models import Changeset

from schemanizer.logic import (
    privileges_logic)
from schemaversions.models import SchemaVersion
from users.models import User
from utils.exceptions import PrivilegeError
from utils.helpers import get_model_instance

log = logging.getLogger(__name__)

MSG_CHANGESET_REVIEW_NOT_ALLOWED = (
    u'User {user} is not allowed to review changeset [ID:{changeset_id}].')


class ChangesetReviewThread(threading.Thread):
    """Runs changeset review logic in a thread."""

    def __init__(self, changeset, schema_version, user):
        """Initializes object."""
        super(ChangesetReviewThread, self).__init__()

        self.daemon = True
        self._changeset = get_model_instance(changeset, Changeset)
        self._schema_version = get_model_instance(
            schema_version, SchemaVersion)
        self._user = get_model_instance(user, User)

        self._init_run_vars()

    def _init_run_vars(self):
        """Initializes variables used when thread runs."""

        self._messages = []
        self._errors = []
        self._has_errors = False

        self._changeset_tests = []
        self._changeset_validations = []

        self._changeset_test_ids = []
        self._changeset_validation_ids = []

        self._review_results_url = None

    @property
    def messages(self):
        """Returns messages."""
        return self._messages

    @property
    def errors(self):
        """Returns error messages."""
        return self._errors

    @property
    def has_errors(self):
        """Returns a boolean value indicating if errors are present."""
        return self._has_errors

    @property
    def changeset_tests(self):
        """Returns changeset tests."""
        return self._changeset_tests

    @property
    def changeset_validations(self):
        """Returns changeset validations."""
        return self._changeset_validations

    @property
    def changeset_test_ids(self):
        """Returns changeset test IDS."""
        return self._changeset_test_ids

    @property
    def changeset_validation_ids(self):
        """Returns changeset validation IDs."""
        return self.changeset_validation_ids

    @property
    def review_results_url(self):
        """Returns review results URL."""
        return self._review_results_url

    def _store_message(self, message, message_type='info'):
        """Stores message."""
        self._messages.append(dict(
            message=message, message_type=message_type))
        if message_type == 'error':
            self._errors.append(dict(
                message=message, message_type='error'))

    def _message_callback(self, obj, message, message_type):
        """Message callback.

        This is provided to allow thread to take a look at the messages
        even when the ChangesetReview logic run has not yet completed.
        """
        self._store_message(message, message_type)

    def run(self):
        self._init_run_vars()

        msg = 'Changeset review thread started.'
        log.info(msg)
        self._store_message(msg)
        try:
            changeset_review = ChangesetReview(
                self._changeset, self._schema_version, self._user,
                message_callback=self._message_callback)
            changeset_review.run()

            self._changeset_tests = changeset_review.changeset_tests
            self._changeset_test_ids = changeset_review.changeset_test_ids
            self._changeset_validations = changeset_review.changeset_validations
            self._changeset_validation_ids = changeset_review.changeset_validation_ids

            # overwrite existing messages recorded by callback
            self._messages = changeset_review.messages
            self._errors = changeset_review.errors
            self._has_errors = changeset_review.has_errors
            self._review_results_url = changeset_review.review_results_url

        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            log.exception(msg)
            self._store_message(msg, 'error')

        finally:
            msg = 'Changeset review thread ended.'
            log.info(msg)
            self._store_message(msg)


def start_changeset_review_thread(changeset, schema_version, user):
    """Reviews changeset."""

    changeset = get_model_instance(changeset, Changeset)
    schema_version = get_model_instance(
        schema_version, SchemaVersion)
    user = get_model_instance(user, User)

    #if changeset_can_be_reviewed_by_user(changeset, user):
    #    thread = ReviewThread(changeset, schema_version, request_id, user, server)
    #    thread.start()
    #    return thread
    if privileges_logic.can_user_review_changeset(user, changeset):
        thread = ChangesetReviewThread(changeset, schema_version, user)
        thread.start()
        return thread
    else:
        raise PrivilegeError(
            u'User is not allowed to set review status to \'in_progress\'.')




