import logging
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils import timezone
from emails import tasks as emails_tasks
from schemanizer.logic import ec2_logic, mysql_logic, changeset_test_logic
from users import models as users_models
from schemaversions import models as schemaversions_models
from changesets import models as changesets_models
from changesettests import models as changesettests_models
from changesetvalidations import models as changesetvalidations_models
from changesettests import changeset_testing
from utils import exceptions
from . import models, event_handlers


log = logging.getLogger(__name__)
MSG_NO_VERSION_FOUND_FOR_SCHEMA = (
    u"No schema version found for database schema '%s'.")


class ChangesetReview(object):
    """Logic for changeset review."""

    def __init__(
            self, changeset, schema_version, reviewed_by,
            message_callback=None, task_id=None, no_ec2=None):

        super(ChangesetReview, self).__init__()

        self.changeset = changeset
        self.schema_version = schema_version
        self.reviewed_by = reviewed_by
        if no_ec2 is None:
            no_ec2 = settings.DEV_NO_EC2_APPLY_CHANGESET
        self.no_ec2 = no_ec2
        self.message_callback = message_callback
        self.task_id = task_id

        self.changeset_review = None
        self.messages = []
        self.has_errors = False
        self.errors = []
        self.changeset_tests = []
        self.changeset_validations = []
        self.changeset_test_ids = []
        self.changeset_validation_ids = []
        self.review_results_url = None

    def store_message(self, message, message_type='info'):
        """Stores message."""
        self.messages.append(dict(
            message=message,
            message_type=message_type))
        if message_type == 'error':
            self.errors.append(dict(
                message=message,
                message_type=message_type
            ))
        if self.message_callback:
            self.message_callback(message, message_type)

    def run(self):
        """Wraps run_impl() in a try except block."""
        try:
            self.run_impl()
        except:
            log.exception('EXCEPTION')
            raise

    def run_impl(self):
        """Starts changeset review."""

        ec2_instance_starter = None
        try:
            # Delete existing changeset review data.
            models.ChangesetReview.objects.filter(
                changeset=self.changeset).delete()

            # Create changeset action entry.
            changesets_models.ChangesetAction.objects.create(
                changeset=self.changeset,
                type=changesets_models.ChangesetAction.TYPE_REVIEW_STARTED,
                timestamp=timezone.now())

            if not self.no_ec2:
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
                    message_callback=self.message_callback,
                )
                ec2_instance_starter.run()
                if ec2_instance_starter.instance and not (
                        ec2_instance_starter.instance.state == 'running'):
                    raise exceptions.Error(
                        'Instance did not reach \'running\' state.')

            if self.no_ec2 or (
                    ec2_instance_starter.instance and
                    ec2_instance_starter.instance.state == 'running'):
                if not self.no_ec2:
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
                    message_callback=self.message_callback
                )
                conn = connection_tester.run()
                if not conn:
                    raise exceptions.Error('Unable to connect to MySQL server.')

                now = timezone.now()

                test_results = changeset_testing.run_tests(
                    changeset=self.changeset,
                    schema_version=self.schema_version,
                    connection_options=connection_options,
                    message_callback=self.message_callback
                )
                syntax_test_result = test_results['syntax']

                structure_after = syntax_test_result['structure_after']
                hash_after = syntax_test_result['hash_after']
                self.changeset_tests = syntax_test_result['changeset_tests']
                for changeset_test in self.changeset_tests:
                    self.changeset_test_ids.append(changeset_test.id)
                if syntax_test_result['has_errors']:
                    self.has_errors = True
                    changesets_models.ChangesetAction.objects.create(
                        changeset=self.changeset,
                        type=changesets_models.ChangesetAction.TYPE_TESTS_FAILED,
                        timestamp=timezone.now())
                else:
                    changesets_models.ChangesetAction.objects.create(
                        changeset=self.changeset,
                        type=changesets_models.ChangesetAction.TYPE_TESTS_PASSED,
                        timestamp=timezone.now())

                # clear existing changeset validations
                changesetvalidations_models.ChangesetValidation.objects.filter(
                    changeset=self.changeset).delete()

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
                # if not self.has_errors:
                #     try:
                #         after_version = schemaversions_models.SchemaVersion.objects.get(
                #             database_schema=self.schema_version.database_schema,
                #             checksum=hash_after)
                #         after_version.ddl = structure_after
                #         after_version.save()
                #     except ObjectDoesNotExist:
                #         after_version = schemaversions_models.SchemaVersion.objects.create(
                #             database_schema=self.schema_version.database_schema,
                #             ddl=structure_after,
                #             checksum=hash_after
                #         )
                #         log.debug('Created new schema version, checksum=%s.' % (
                #             hash_after,))
                # else:
                #     after_version = None

                if self.has_errors:
                    self.changeset.review_status = (
                        changesets_models.Changeset.REVIEW_STATUS_REJECTED)
                else:
                    self.changeset.review_status = (
                        changesets_models.Changeset.REVIEW_STATUS_IN_PROGRESS)
                self.changeset.reviewed_by = self.reviewed_by
                self.changeset.reviewed_at = timezone.now()
                #self.changeset.before_version = self.schema_version
                #self.changeset.after_version = after_version
                self.changeset.before_version = None
                self.changeset.after_version = None
                self.changeset.save()

                if (
                        self.changeset.review_status ==
                        changesets_models.Changeset.REVIEW_STATUS_REJECTED):
                    # Create entry on changeset actions.
                    changesets_models.ChangesetAction.objects.create(
                        changeset=self.changeset,
                        type=changesets_models.ChangesetAction.TYPE_REJECTED,
                        timestamp=timezone.now())

                changeset_test_ids_string = u','.join(
                    [str(obj.id) for obj in self.changeset_tests])
                changeset_validation_ids_string = u','.join(
                    [str(obj.id) for obj in self.changeset_validations])
                site = Site.objects.get_current()
                url = reverse(
                    'changesetreviews_result',
                    args=[self.changeset.id])
                self.review_results_url = 'http://%s%s' % (
                    site.domain, url)

                models.ChangesetReview.objects.create(
                    changeset=self.changeset,
                    schema_version=self.schema_version,
                    results_log='',
                    success=not self.has_errors)

                log.info('Changeset was reviewed, id=%s.' % (
                    self.changeset.pk,))


        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            log.exception(msg)
            self.has_errors = True
            models.ChangesetReview.objects.create(
                changeset=self.changeset,
                schema_version=self.schema_version,
                results_log=msg, success=False)

        finally:
            if ec2_instance_starter:
                ec2_instance_starter.terminate_instances()

            # Create changeset action entry.
            changesets_models.ChangesetAction.objects.create(
                changeset=self.changeset,
                type=changesets_models.ChangesetAction.TYPE_REVIEWED,
                timestamp=timezone.now())

            msg = 'Changeset review ended.'
            log.info(msg)
            self.store_message(msg)


def review_changeset(
        changeset, schema_version=None, reviewed_by=None,
        message_callback=None, request=None, task_id=None):
    """Reviews changeset."""
    database_schema = changeset.database_schema

    if not schema_version:
        # use the latest schema version if not specified
        schema_version_qs = (
            schemaversions_models.SchemaVersion.objects.filter(
                database_schema=database_schema)
            .order_by('-updated_at', '-id'))
        if not schema_version_qs.exists():
            raise exceptions.Error(
                MSG_NO_VERSION_FOUND_FOR_SCHEMA % (database_schema.name,))
        schema_version = schema_version_qs[0]

    # overwrite reviewed_by if request object is present
    if request:
        reviewed_by = request.user.schemanizer_user

    if not reviewed_by:
        # use default user if not specified
        reviewed_by = users_models.User.objects.get(
            name=settings.DEFAULT_CHANGESET_ACTION_USERNAME)

    changeset_review = ChangesetReview(
        changeset=changeset, schema_version=schema_version,
        reviewed_by=reviewed_by,
        message_callback=message_callback,
        task_id=task_id)
    changeset_review.run()

    event_handlers.on_changeset_reviewed(changeset)

    return changeset_review