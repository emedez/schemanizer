import itertools
import logging
import pprint
import string
import threading

from django.conf import settings
from django.db import transaction
from django.utils import timezone
import MySQLdb
import sqlparse

from schemanizer import exceptions, models, utils
from schemanizer.logic import mail_logic, privileges_logic

log = logging.getLogger(__name__)


class ChangesetApply(object):
    """Changeset apply logic."""

    def __init__(
            self, changeset, user, server, connection_options=None,
            message_callback=None):
        """Initializes instance."""

        super(ChangesetApply, self).__init__()

        self._changeset = utils.get_model_instance(changeset, models.Changeset)
        self._user = utils.get_model_instance(user, models.User)
        self._server = utils.get_model_instance(server, models.Server)
        if connection_options is None:
            connection_options = {}
        self._connection_options = connection_options
        self._message_callback = message_callback

        self._connection_options.update({
            'host': self._server.hostname,
            'db': self._changeset.database_schema.name
        })
        if self._server.port:
            self._connection_options['port'] = self._server.port

        self._init_run_vars()

    def _init_run_vars(self):
        """Additional instance attributes."""

        self._messages = []
        self._has_errors = False
        self._changeset_detail_applies = []
        self._changeset_detail_apply_ids = []

    @property
    def messages(self):
        """Returns messages."""
        return self._messages

    @property
    def has_errors(self):
        """Returns a boolean value indicating if error(s) had occurred."""
        return self._has_errors

    @property
    def changeset_detail_applies(self):
        return self._changeset_detail_applies

    @property
    def changeset_detail_apply_ids(self):
        return self._changeset_detail_apply_ids

    def _store_message(self, message, message_type='info'):
        """Stores message."""
        self._messages.append(dict(
            message=message,
            message_type=message_type))
        if self._message_callback:
            self._message_callback(message, message_type)

    def _apply_changeset_detail(self, changeset_detail, cursor):
        has_errors = False
        results_logs = []

        try:
            counts_before = None
            if (
                    changeset_detail.apply_verification_sql and
                    changeset_detail.apply_verification_sql.strip()):
                counts_before = utils.execute_count_statements(
                    cursor, changeset_detail.apply_verification_sql)
                log.debug('Row count(s) before apply_sql: %s' % (
                    counts_before,))

            queries = sqlparse.split(changeset_detail.apply_sql)
            log.debug(
                'connection options:\n%s' % (
                    pprint.pformat(self._connection_options),))
            self._store_message(
                u'apply_sql: %s' % (changeset_detail.apply_sql,))
            for query in queries:
                query = query.rstrip(string.whitespace + ';')
                log.debug(u'apply_sql: %s' % (query,))
                try:
                    if query:
                        cursor.execute(query)
                except Exception, e:
                    msg = 'ERROR %s: %s' % (type(e), e)
                    log.exception(msg)
                    self._store_message(msg, 'error')
                    results_logs.append(msg)
                    has_errors = True
                    break
                finally:
                    while cursor.nextset() is not None:
                        pass

            counts_after = None
            if (
                    changeset_detail.apply_verification_sql and
                    changeset_detail.apply_verification_sql.strip()):
                counts_after = utils.execute_count_statements(
                    cursor, changeset_detail.apply_verification_sql)
                log.debug('Row count(s) after apply_sql: %s' % (
                    counts_after,))

            if counts_before is not None and counts_after is not None:
                volumetric_values = u','.join(
                    itertools.imap(
                        lambda before, after:
                        unicode(after - before)
                        if (before is not None and after is not None)
                        else '',
                        counts_before, counts_after))
                if volumetric_values != changeset_detail.volumetric_values:
                    msg = (
                        'Volumetric values "%s" is different from expected '
                        'value "%s"' % (
                            volumetric_values,
                            changeset_detail.volumetric_values))
                    log.error(msg)
                    self._store_message(msg, 'error')
                    results_logs.append(msg)
                    has_errors = True

        finally:
            results_log = '\n'.join(results_logs)
            changeset_detail_apply = models.ChangesetDetailApply.objects.create(
                changeset_detail=changeset_detail,
                environment=self._server.environment,
                server=self._server,
                results_log=results_log)
            #conn.close()

        return dict(
            has_errors=has_errors,
            changeset_detail_apply=changeset_detail_apply)

    def _apply_changeset_details(self):
        conn = MySQLdb.connect(**self._connection_options)
        cursor = conn.cursor()
        try:
            for changeset_detail in (
                    self._changeset.changeset_details.all().order_by('id')
                    ):
                ret = self._apply_changeset_detail(
                    changeset_detail, cursor)
                if ret['has_errors']:
                    self._has_errors = True
                self._changeset_detail_applies.append(
                    ret['changeset_detail_apply'])
                self._changeset_detail_apply_ids.append(
                    ret['changeset_detail_apply'].id)
        finally:
            cursor.execute('FLUSH TABLES')
            cursor.close()
            conn.close()

    def run(self):
        self._init_run_vars()

        try:
            if models.ChangesetApply.objects.filter(
                    changeset=self._changeset, server=self._server).exists():
                raise exceptions.Error(
                    "Changeset has been applied already at server '%s'." % (
                        self._server.name,))

            ddl = utils.mysql_dump(**self._connection_options)
            checksum = utils.schema_hash(ddl)
            if not (self._changeset.before_version and
                    self._changeset.before_version.checksum == checksum):
                before_version_checksum = None
                if self._changeset.before_version:
                    before_version_checksum = self._changeset.before_version.checksum
                log.debug('checksum = %s' % (checksum,))
                log.debug('before_version = %s' % (self._changeset.before_version,))
                raise exceptions.Error(
                    u"Cannot apply changeset, existing schema checksum '%s' "
                    u"on host does not match the expected value '%s'." % (
                        checksum, before_version_checksum))

            with transaction.commit_on_success():
                self._apply_changeset_details()

                ddl = utils.mysql_dump(**self._connection_options)
                log.debug('DDL:\n%s' % (ddl,))
                checksum = utils.schema_hash(ddl)
                if not (self._changeset.after_version and (
                        self._changeset.after_version.checksum == checksum)):
                    log.debug('checksum = %s' % (checksum,))
                    log.debug('after_version = %s' % (
                        self._changeset.after_version,))
                    raise exceptions.Error(
                        'Final schema checksum does not match the expected '
                        'value.')

                applied_at = timezone.now()
                changeset_apply = models.ChangesetApply.objects.create(
                    changeset=self._changeset, server=self._server,
                    applied_at=applied_at, applied_by=self._user)
                changeset_action = models.ChangesetAction.objects.create(
                    changeset=self._changeset,
                    type=models.ChangesetAction.TYPE_APPLIED,
                    timestamp=applied_at)
                models.ChangesetActionServerMap.objects.create(
                    changeset_action=changeset_action, server=self._server)

            mail_logic.send_changeset_applied_mail(
                self._changeset, changeset_apply)

        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            log.exception(msg)
            self._store_message(msg, 'error')
            self._has_errors = True


class ChangesetApplyThread(threading.Thread):
    def __init__(self, changeset, user, server, connection_options,):
        super(ChangesetApplyThread, self).__init__()
        self.daemon = True

        self.changeset = utils.get_model_instance(changeset, models.Changeset)
        self.user = utils.get_model_instance(user, models.User)
        self.server = utils.get_model_instance(server, models.Server)
        self.connection_options = connection_options

        self.messages = []

        self.has_errors = False
        self.changeset_detail_applies = []
        self.changeset_detail_apply_ids = []

    def _store_message(self, message, message_type='info'):
        """Stores message."""
        self.messages.append(dict(
            message=message, message_type=message_type))

    def _message_callback(self, obj, message, message_type):
        """Message callback.

        This is provided to allow thread to take a look at the messages
        even when the ChangesetApply logic run has not yet completed.
        """
        self._store_message(message, message_type)

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
    changeset = utils.get_model_instance(changeset, models.Changeset)
    user = utils.get_model_instance(user, models.User)
    server = utils.get_model_instance(server, models.Server)

    if not privileges_logic.can_user_apply_changeset(user, changeset):
        raise exceptions.PrivilegeError(
            'User is not allowed to apply changeset.')

    connection_options = {}
    if settings.AWS_MYSQL_USER:
        connection_options['user'] = settings.AWS_MYSQL_USER
    if settings.AWS_MYSQL_PASSWORD:
        connection_options['passwd'] = settings.AWS_MYSQL_PASSWORD

    thread = ChangesetApplyThread(changeset, user, server, connection_options)
    thread.start()
    return thread


def apply_changeset(changeset, user, server, message_callback=None):
    """Applies changeset to specified server."""

    changeset = utils.get_model_instance(changeset, models.Changeset)
    user = utils.get_model_instance(user, models.User)
    server = utils.get_model_instance(server, models.Server)

    if not privileges_logic.can_user_apply_changeset(user, changeset):
        raise exceptions.PrivilegeError(
            'User is not allowed to apply changeset.')

    connection_options = {}
    if settings.AWS_MYSQL_USER:
        connection_options['user'] = settings.AWS_MYSQL_USER
    if settings.AWS_MYSQL_PASSWORD:
        connection_options['passwd'] = settings.AWS_MYSQL_PASSWORD

    changeset_apply_obj = ChangesetApply(
        changeset, user, server, connection_options, message_callback)
    changeset_apply_obj.run()

    return changeset_apply_obj