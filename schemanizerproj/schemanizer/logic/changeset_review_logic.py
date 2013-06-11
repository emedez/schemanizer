import logging
import threading
import urllib

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.utils import timezone

from schemanizer import models, exceptions, utils
from schemanizer.logic import (
    changeset_test_logic,
    changeset_validation_logic,
    ec2_logic,
    mail_logic,
    mysql_logic,
    privileges_logic)

log = logging.getLogger(__name__)

MSG_CHANGESET_REVIEW_NOT_ALLOWED = (
    u'User {user} is not allowed to review changeset [ID:{changeset_id}].')
MSG_NO_VERSION_FOUND_FOR_SCHEMA = (
    u"No schema version found for database schema '%s'.")


class ChangesetReview(object):
    """Logic for changeset review."""

    def __init__(
            self, changeset, schema_version, user, message_callback=None,
            send_mail=True):
        """Initializes object.

        Args:

            changeset: Changeset ID or instance of Changeset.

            user: User ID or instance of User.

            no_ec2_instance_launch: for development use only, If True, will
                not launch an EC2 instance but will instead use localhost for
                the review process.

        """
        super(ChangesetReview, self).__init__()

        self._changeset = utils.get_model_instance(changeset, models.Changeset)
        self._schema_version = utils.get_model_instance(
            schema_version, models.SchemaVersion)
        self._user = utils.get_model_instance(user, models.User)
        self._no_ec2_instance_launch = settings.DEV_NO_EC2_APPLY_CHANGESET
        self._message_callback = message_callback
        self._send_mail = send_mail

        self._init_run_vars()

    def _init_run_vars(self):
        """Initializes variables needed in running logic."""
        self._messages = []
        self._has_errors = False
        self._errors = []
        self._changeset_tests = []
        self._changeset_validations = []
        self._changeset_test_ids = []
        self._changeset_validation_ids = []
        self._review_results_url = None

    @property
    def has_errors(self):
        """Returns a boolean value indicating if errors occurred."""
        return self._has_errors

    @property
    def errors(self):
        """Returns stored error messages."""
        return self._errors

    @property
    def messages(self):
        """Returns messages."""
        return self._messages

    @property
    def changeset_tests(self):
        """Returns results of changeset syntax test."""
        return self._changeset_tests

    @property
    def changeset_validations(self):
        """Returns result of changeset validation."""
        return self._changeset_validations

    @property
    def changeset_test_ids(self):
        """Returns IDs of changeset syntax test."""
        return self._changeset_test_ids

    @property
    def changeset_validation_ids(self):
        """Returns IDs of changeset validation."""
        return self._changeset_validation_ids

    @property
    def review_results_url(self):
        """Returns review results URL."""
        return self._review_results_url

    def _store_message(self, message, message_type='info'):
        """Stores message."""
        self._messages.append(dict(
            message=message,
            message_type=message_type))
        if message_type == 'error':
            self._errors.append(dict(
                message=message,
                message_type=message_type
            ))
        if self._message_callback:
            self._message_callback(message, message_type)

    def run(self):
        """Wraps run_impl() in a try except block."""
        try:
            self._run_impl()
        except:
            log.exception('EXCEPTION')
            raise

    def _run_impl(self):
        """Starts changeset review."""

        self._init_run_vars()
        if not privileges_logic.can_user_review_changeset(
                self._user, self._changeset):
            raise exceptions.PrivilegeError(
                MSG_CHANGESET_REVIEW_NOT_ALLOWED.format(
                    user=self._user.auth_user.username,
                    changeset_id=self._changeset.id))

        # Create changeset action entry.
        models.ChangesetAction.objects.create(
            changeset=self._changeset,
            type=models.ChangesetAction.TYPE_REVIEW_STARTED,
            timestamp=timezone.now())

        ec2_instance_starter = None
        try:
            if not self._no_ec2_instance_launch:
                ec2_instance_starter = ec2_logic.EC2InstanceStarter(
                    region=settings.AWS_REGION,
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    ami_id=settings.AWS_AMI_ID,
                    key_name=settings.AWS_KEY_NAME,
                    instance_type=settings.AWS_INSTANCE_TYPE,
                    security_groups=settings.AWS_SECURITY_GROUPS,
                    running_state_check_pre_delay=settings.AWS_EC2_INSTANCE_START_WAIT,
                    running_state_check_timeout=settings.AWS_EC2_INSTANCE_STATE_CHECK_TIMEOUT,
                    message_callback=self._message_callback,
                )
                ec2_instance_starter.run()
                if ec2_instance_starter.instance and not (
                        ec2_instance_starter.instance.state == 'running'):
                    raise exceptions.Error(
                        'Instance did not reach \'running\' state.')

            if self._no_ec2_instance_launch or (
                    ec2_instance_starter.instance and
                    ec2_instance_starter.instance.state == 'running'):
                if not self._no_ec2_instance_launch:
                    host = ec2_instance_starter.instance.public_dns_name
                else:
                    host = None

                connection_options = {}
                if host:
                    connection_options['host'] = host
                if settings.AWS_MYSQL_PORT:
                    connection_options['port'] = settings.AWS_MYSQL_PORT
                if settings.AWS_MYSQL_USER:
                    connection_options['user'] = settings.AWS_MYSQL_USER
                if settings.AWS_MYSQL_PASSWORD:
                    connection_options['passwd'] = settings.AWS_MYSQL_PASSWORD

                connection_tester = mysql_logic.MySQLServerConnectionTester(
                    connection_options=connection_options,
                    connect_pre_delay=settings.AWS_MYSQL_START_WAIT,
                    connect_timeout=settings.AWS_MYSQL_CONNECT_TIMEOUT,
                    message_callback=self._message_callback
                )
                conn = connection_tester.run()
                if not conn:
                    raise exceptions.Error('Unable to connect to MySQL server.')

                now = timezone.now()
                # Create changeset action entry.
                # models.ChangesetAction.objects.create(
                #     changeset=self._changeset,
                #     type=models.ChangesetAction.TYPE_REVIEWED,
                #     timestamp=now)

                # clear existing changeset tests
                models.ChangesetTest.objects.filter(
                    changeset_detail__changeset=self._changeset).delete()

                syntax_test = changeset_test_logic.ChangesetSyntaxTest(
                    changeset=self._changeset,
                    schema_version=self._schema_version,
                    connection_options=connection_options,
                    message_callback=self._message_callback
                )
                syntax_test.run()
                structure_after = syntax_test.structure_after
                hash_after = syntax_test.hash_after
                self._changeset_tests = syntax_test.changeset_tests
                for changeset_test in self._changeset_tests:
                    self._changeset_test_ids.append(changeset_test.id)
                if syntax_test.has_errors:
                    self._has_errors = True
                    models.ChangesetAction.objects.create(
                        changeset=self._changeset,
                        type=models.ChangesetAction.TYPE_TESTS_FAILED,
                        timestamp=timezone.now())
                else:
                    models.ChangesetAction.objects.create(
                        changeset=self._changeset,
                        type=models.ChangesetAction.TYPE_TESTS_PASSED,
                        timestamp=timezone.now())

                # clear existing changeset validations
                models.ChangesetValidation.objects.filter(
                    changeset=self._changeset).delete()

                #validation_results = (
                #    changeset_validation_logic
                #        .changeset_validate_no_update_with_where_clause(
                #            self._changeset, self._user))
                #if validation_results['changeset_validation']:
                #    self._changeset_validations.append(
                #            validation_results['changeset_validation'])
                #    self._changeset_validation_ids.append(
                #        validation_results['changeset_validation'].id)
                #if validation_results['has_errors']:
                #    self._has_errors = True

                #
                # Update changeset.
                #
                if not self._has_errors:
                    try:
                        after_version = models.SchemaVersion.objects.get(
                            database_schema=self._schema_version.database_schema,
                            checksum=hash_after)
                        after_version.ddl = structure_after
                        after_version.save()
                    except ObjectDoesNotExist:
                        after_version = models.SchemaVersion.objects.create(
                            database_schema=self._schema_version.database_schema,
                            ddl=structure_after,
                            checksum=hash_after
                        )
                        log.debug('Created new schema version, checksum=%s.' % (
                            hash_after,))
                else:
                    after_version = None

                if self._has_errors:
                    self._changeset.review_status = (
                        models.Changeset.REVIEW_STATUS_REJECTED)
                else:
                    self._changeset.review_status = (
                        models.Changeset.REVIEW_STATUS_IN_PROGRESS)
                self._changeset.reviewed_by = self._user
                self._changeset.reviewed_at = now
                self._changeset.before_version = self._schema_version
                self._changeset.after_version = after_version
                self._changeset.save()

                if (
                        self._changeset.review_status ==
                        models.Changeset.REVIEW_STATUS_REJECTED):
                    # Create entry on changeset actions.
                    models.ChangesetAction.objects.create(
                        changeset=self._changeset,
                        type=models.ChangesetAction.TYPE_REJECTED,
                        timestamp=timezone.now())

                changeset_test_ids_string = u','.join(
                    [str(obj.id) for obj in self._changeset_tests])
                changeset_validation_ids_string = u','.join(
                    [str(obj.id) for obj in self._changeset_validations])
                site = Site.objects.get_current()
                url = reverse(
                    'schemanizer_changeset_view_review_results',
                    args=[self._changeset.id])
                #query_string = urllib.urlencode(dict(
                #    changeset_validation_ids=changeset_validation_ids_string,
                #    changeset_test_ids=changeset_test_ids_string))
                #self._review_results_url = 'http://%s%s?%s' % (
                #    site.domain,
                #    url,
                #    query_string)
                self._review_results_url = 'http://%s%s' % (
                    site.domain, url)

                log.info('Changeset was reviewed, id=%s.' % (
                    self._changeset.id,))
                try:
                    if self._send_mail:
                        mail_logic.send_mail_changeset_reviewed(
                            self._changeset)
                except Exception, e:
                    msg = 'ERROR %s: %s'  % (type(e), e)
                    log.exception(msg)
                    self._store_message(msg, 'error')
        finally:
            if ec2_instance_starter:
                ec2_instance_starter.terminate_instances()

            # Create changeset action entry.
            models.ChangesetAction.objects.create(
                changeset=self._changeset,
                type=models.ChangesetAction.TYPE_REVIEWED,
                timestamp=timezone.now())

            msg = 'Changeset review ended.'
            log.info(msg)
            self._store_message(msg)


class ChangesetReviewThread(threading.Thread):
    """Runs changeset review logic in a thread."""

    def __init__(self, changeset, schema_version, user):
        """Initializes object."""
        super(ChangesetReviewThread, self).__init__()

        self.daemon = True
        self._changeset = utils.get_model_instance(changeset, models.Changeset)
        self._schema_version = utils.get_model_instance(
            schema_version, models.SchemaVersion)
        self._user = utils.get_model_instance(user, models.User)

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

    changeset = utils.get_model_instance(changeset, models.Changeset)
    schema_version = utils.get_model_instance(
        schema_version, models.SchemaVersion)
    user = utils.get_model_instance(user, models.User)

    #if changeset_can_be_reviewed_by_user(changeset, user):
    #    thread = ReviewThread(changeset, schema_version, request_id, user, server)
    #    thread.start()
    #    return thread
    if privileges_logic.can_user_review_changeset(user, changeset):
        thread = ChangesetReviewThread(changeset, schema_version, user)
        thread.start()
        return thread
    else:
        raise exceptions.PrivilegeError(
            u'User is not allowed to set review status to \'in_progress\'.')


def review_changeset(
        changeset, schema_version=None, user=None, message_callback=None):
    """Reviews changeset."""

    from schemanizer import tasks

    changeset = utils.get_model_instance(changeset, models.Changeset)
    database_schema = changeset.database_schema

    if schema_version is None:
        # use the latest schema version if not specified
        schema_version_qs = (
            models.SchemaVersion.objects.filter(
                database_schema=database_schema)
            .order_by('-created_at', '-id'))
        if not schema_version_qs.exists():
            raise exceptions.Error(
                MSG_NO_VERSION_FOUND_FOR_SCHEMA % (database_schema.name,))
        schema_version = schema_version_qs[0]
    else:
        schema_version = utils.get_model_instance(
            schema_version, models.SchemaVersion)

    if user is None:
        # use default user if not specified
        user = models.User.objects.get(
            name=settings.DEFAULT_CHANGESET_ACTION_USERNAME)
    else:
        user = utils.get_model_instance(user, models.User)

    changeset_review = ChangesetReview(
        changeset, schema_version, user, send_mail=False,
        message_callback=message_callback)
    changeset_review.run()

    tasks.send_mail_changeset_reviewed.delay(changeset)

    return changeset_review

