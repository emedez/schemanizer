import difflib
import logging
import string
import MySQLdb
from django.conf import settings
from django.utils import timezone
import sqlparse
from changesets import models as changesets_models
from schemaversions import models as schemaversions_models
from utils import exceptions, mysql_functions
from . import models, event_handlers
from schemanizer.logic import privileges_logic

log = logging.getLogger(__name__)


def apply_changeset(changeset, applied_by, server, message_callback=None,
                    task_id=None, request=None):
    """Applies changeset to specified server."""

    if not privileges_logic.can_user_apply_changeset(applied_by, changeset):
        raise exceptions.PrivilegeError(
            'User is not allowed to apply changeset.')

    connection_options = {}
    if settings.MYSQL_USER:
        connection_options['user'] = settings.MYSQL_USER
    if settings.MYSQL_PASSWORD:
        connection_options['passwd'] = settings.MYSQL_PASSWORD

    changeset_apply_obj = ChangesetApply(changeset, applied_by, server,
                                         connection_options, message_callback,
                                         task_id=task_id, request=request)
    changeset_apply_obj.run()

    return changeset_apply_obj


class ChangesetApply(object):
    """Changeset apply logic."""

    def __init__(self, changeset, applied_by, server, connection_options=None,
                 message_callback=None, task_id=None, request=None):
        """Initializes instance."""

        super(ChangesetApply, self).__init__()

        self.changeset = changeset
        self.applied_by = applied_by
        self.server = server
        if connection_options is None:
            connection_options = {}
        self.connection_options = connection_options
        self.message_callback = message_callback

        self.connection_options.update({
            'host': self.server.hostname,
            'db': self.changeset.database_schema.name
        })
        if self.server.port:
            self.connection_options['port'] = self.server.port

        self.task_id = task_id
        self.request = request

        self.messages = []
        self.has_errors = False
        self.changeset_detail_applies = []
        self.changeset_detail_apply_ids = []

    def store_message(self, message, message_type='info', extra=None):
        """Stores message."""
        self.messages.append(dict(
            message=message,
            message_type=message_type,
            extra=extra))
        if self.message_callback:
            self.message_callback(message, message_type, extra)

    def apply_changeset_detail(self, changeset_detail, cursor):
        has_errors = False
        results_logs = []

        try:
            log.debug(
                u'Applying changeset detail [id=%s]...', changeset_detail.pk)

            #
            # Execute apply_sql
            #
            log.debug(
                u'Executing apply_sql:\n%s', changeset_detail.apply_sql)
            queries = sqlparse.split(changeset_detail.apply_sql)
            self.store_message(
                u'apply_sql: %s' % (changeset_detail.apply_sql,))
            for query in queries:
                query = query.rstrip(string.whitespace + ';')
                try:
                    if query:
                        cursor.execute(query)
                except Exception, e:
                    msg = 'ERROR %s: %s' % (type(e), e)
                    log.exception(msg)
                    self.store_message(msg, 'error')
                    results_logs.append(msg)
                    has_errors = True
                    break
                finally:
                    while cursor.nextset() is not None:
                        pass

        finally:
            results_log = '\n'.join(results_logs)
            changeset_detail_apply = (
                models.ChangesetDetailApply.objects.create(
                    changeset_detail=changeset_detail,
                    environment=self.server.environment,
                    server=self.server,
                    results_log=results_log))

        return dict(
            has_errors=has_errors,
            changeset_detail_apply=changeset_detail_apply)

    def apply_changeset_details(self):
        conn = MySQLdb.connect(**self.connection_options)
        cursor = conn.cursor()
        try:
            for changeset_detail in (
                    self.changeset.changesetdetail_set.all().order_by('id')):
                ret = self.apply_changeset_detail(
                    changeset_detail, cursor)
                if ret['has_errors']:
                    self.has_errors = True
                self.changeset_detail_applies.append(
                    ret['changeset_detail_apply'])
                self.changeset_detail_apply_ids.append(
                    ret['changeset_detail_apply'].id)
        finally:
            cursor.execute('FLUSH TABLES')
            cursor.close()
            conn.close()

    def run(self):
        try:
            if models.ChangesetApply.objects.filter(
                    changeset=self.changeset, server=self.server,
                    success=True).exists():
                raise exceptions.Error(
                    "Changeset has been successfully applied already at "
                    "server '%s'." % (
                        self.server.name,))

            host_before_ddl = mysql_functions.dump_schema(
                **self.connection_options)
            host_before_checksum = mysql_functions.generate_schema_hash(
                host_before_ddl)
            schema_version_before_apply = None

            #
            # If changeset does not have a before_version yet,
            # then it is the first time the changeset is being applied,
            # ensure that db on host has a known schema version.
            #
            if not self.changeset.before_version:
                schema_version_qs = schemaversions_models.SchemaVersion.objects.filter(
                    database_schema=self.changeset.database_schema,
                    checksum=host_before_checksum)
                if not schema_version_qs.exists():
                    raise exceptions.Error('Schema version on host is unknown.')
                else:
                    # Remember this version
                    schema_version_before_apply = schema_version_qs[0]

            #
            # If not first time to apply, check that the host schema version
            # is the same as what the changeset expects.
            #
            elif self.changeset.before_version.checksum != host_before_checksum:
                before_version_checksum = self.changeset.before_version.checksum
                before_version_ddl = self.changeset.before_version.ddl
                before_version_ddl_lines = before_version_ddl.splitlines(True)
                current_ddl_lines = host_before_ddl.splitlines(True)
                delta = [
                    line for line in difflib.context_diff(
                        before_version_ddl_lines, current_ddl_lines,
                        fromfile='expected', tofile='actual')]
                msg = (
                    u"Cannot apply changeset, existing schema on host "
                    u"does not match the expected schema.")
                raise exceptions.SchemaDoesNotMatchError(
                    msg, before_version_ddl, host_before_ddl, ''.join(delta))

            self.apply_changeset_details()

            host_after_ddl = mysql_functions.dump_schema(
                **self.connection_options)
            host_after_checksum = mysql_functions.generate_schema_hash(
                host_after_ddl)
            schema_version_after_apply = None

            #
            # If changeset is being applied for the first time,
            # record the schema versions -- before and after it is applied.
            #
            if not self.changeset.before_version:
                schema_version_after_apply, created = (
                    schemaversions_models.SchemaVersion.objects.get_or_create(
                        database_schema=self.changeset.database_schema,
                        checksum=host_after_checksum
                    ))
                if created:
                    schema_version_after_apply.ddl = host_after_ddl
                    schema_version_after_apply.pulled_from = self.server
                    schema_version_after_apply.pull_datetime = timezone.now()
                    schema_version_after_apply.save()
                self.changeset.before_version = schema_version_before_apply
                self.changeset.after_version = schema_version_after_apply
                self.changeset.save()

            #
            # If not first time to apply, ensure that final schema version on
            # host is what the changeset expects.
            #
            elif self.changeset.after_version.checksum != host_after_checksum:
                after_version_checksum = self.changeset.after_version.checksum
                after_version_ddl = self.changeset.after_version.ddl
                after_version_ddl_lines = after_version_ddl.splitlines(True)
                current_ddl_lines = host_after_ddl.splitlines(True)
                delta = [
                    line for line in difflib.context_diff(
                        after_version_ddl_lines, current_ddl_lines,
                        fromfile='expected', tofile='actual')]
                msg = (
                    u"Final schema on host does not match the expected "
                    u"schema."
                )
                raise exceptions.SchemaDoesNotMatchError(
                    msg, after_version_ddl, host_after_ddl, ''.join(delta))

            changeset_action = changesets_models.ChangesetAction.objects.create(
                changeset=self.changeset,
                type=changesets_models.ChangesetAction.TYPE_APPLIED,
                timestamp=timezone.now())
            changesets_models.ChangesetActionServerMap.objects.create(
                changeset_action=changeset_action, server=self.server)
            changeset_apply = models.ChangesetApply.objects.create(
                changeset=self.changeset, server=self.server,
                applied_at=timezone.now(), applied_by=self.applied_by,
                success=True,
                changeset_action=changeset_action,
                task_id=self.task_id)

            event_handlers.on_changeset_applied(
                changeset_apply, request=self.request)

        except exceptions.SchemaDoesNotMatchError, e:
            msg = 'ERROR %s: %s' % (type(e), e.message)
            log.exception(msg)
            extra = dict(delta=e.delta)
            self.store_message(msg, 'error', extra)
            self.has_errors = True

            try:
                changeset_action = changesets_models.ChangesetAction.objects.create(
                    changeset=self.changeset,
                    type=changesets_models.ChangesetAction.TYPE_APPLIED_FAILED,
                    timestamp=timezone.now())
                changesets_models.ChangesetActionServerMap.objects.create(
                    changeset_action=changeset_action, server=self.server)
                changeset_apply = models.ChangesetApply.objects.create(
                    changeset=self.changeset, server=self.server,
                    applied_at=timezone.now(), applied_by=self.applied_by,
                    results_log=u'%s\nSchema delta:\n%s' % (msg, e.delta),
                    success=False,
                    changeset_action=changeset_action,
                    task_id=self.task_id)

                event_handlers.on_changeset_apply_failed(
                    changeset_apply, request=self.request)
            except:
                log.exception('EXCEPTION')
                pass

        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            log.exception(msg)
            self.store_message(msg, 'error')
            self.has_errors = True

            try:
                changeset_action = changesets_models.ChangesetAction.objects.create(
                    changeset=self.changeset,
                    type=changesets_models.ChangesetAction.TYPE_APPLIED_FAILED,
                    timestamp=timezone.now())
                changesets_models.ChangesetActionServerMap.objects.create(
                    changeset_action=changeset_action, server=self.server)
                changeset_apply = models.ChangesetApply.objects.create(
                    changeset=self.changeset, server=self.server,
                    applied_at=timezone.now(), applied_by=self.applied_by,
                    results_log=msg,
                    success=False,
                    changeset_action=changeset_action,
                    task_id=self.task_id)

                event_handlers.on_changeset_apply_failed(
                    changeset_apply, request=self.request)
            except:
                log.exception('EXCEPTION')
                pass