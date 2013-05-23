import logging
import string
import warnings

from django.db import transaction
from django.utils import timezone
import MySQLdb
import sqlparse

from schemanizer import exceptions, models, utils

warnings.filterwarnings('ignore', category=MySQLdb.Warning)
log = logging.getLogger(__name__)


class ChangesetSyntaxTest(object):
    """Contains changeset syntax test logic."""

    def __init__(
            self, changeset, schema_version, connection_options=None,
            message_callback=None):
        """Initializes object."""

        super(ChangesetSyntaxTest, self).__init__()

        self._changeset = changeset
        self._schema_version = schema_version
        self._connection_options = connection_options
        self._message_callback = message_callback

        self._init_run_vars()

    def _init_run_vars(self):
        """Initializes variables used when running logic."""
        self._messages = []
        self._changeset_tests = []
        self._has_errors = False
        self._structure_after = None
        self._hash_after = None

    @property
    def messages(self):
        """Returns messages."""
        return self._messages

    @property
    def changeset_tests(self):
        """Returns changeset test results."""
        return self._changeset_tests

    @property
    def has_errors(self):
        """Returns True if test has errors, otherwise False."""
        return self._has_errors

    @property
    def structure_after(self):
        """Returns structure after tests are performed."""
        return self._structure_after

    @property
    def hash_after(self):
        """Returns hash of structure after tests are performed."""
        return self._hash_after

    def _store_message(self, message, message_type='info'):
        """Stores message."""
        self._messages.append(dict(
            message=message,
            message_type=message_type))
        if self._message_callback:
            self._message_callback(self, message, message_type)

    def _execute_query(self, cursor, query):
        """Executes query."""
        statements = sqlparse.split(query)
        for statement in statements:
            statement = statement.rstrip(unicode(string.whitespace + ';'))
            if statement:
                log.debug(statement)
                cursor.execute(statement)
                while cursor.nextset() is not None:
                    pass

    def _execute_count_sql(self, cursor, count_sql):
        """Executes count SQL."""

        count = None
        if count_sql:
            count_sql = count_sql.strip(unicode(
                string.whitespace + ';'))
        if count_sql:
            statements = sqlparse.split(count_sql)
            if len(statements) > 1:
                raise exceptions.Error(
                    'The number of statements for Count SQL  should not be '
                    'greater than 1.')
            statement = statements[0].rstrip(unicode(string.whitespace + ';'))
            if statement:
                log.debug(u'STATEMENT: %s' % (statement,))
                try:
                    cursor.execute(statement)
                    if len(cursor.description) > 1:
                        raise exceptions.Error(
                            'Count SQL should return a single value only.')
                    row = cursor.fetchone()
                    if row is None:
                        raise exceptions.Error('Count SQL result is empty.')
                    count = row[0]
                finally:
                    while cursor.nextset() is not None:
                        pass
        return count

    def run(self):
        """Main logic for testing changeset."""

        self._init_run_vars()

        if (self._changeset.database_schema_id !=
                self._schema_version.database_schema_id):
            msg = 'Schema version and changeset do have the same database schema.'
            log.error(msg)
            self._store_message(msg, 'error')
            self._has_errors = True
            return

        msg = 'Changeset syntax test was started.'
        log.info(msg)
        self._store_message(msg)

        conn = MySQLdb.connect(**self._connection_options)
        schema_name = self._changeset.database_schema.name
        with conn as cursor:
            #
            # Create schema
            #
            cursor.execute('DROP SCHEMA IF EXISTS %s' % (schema_name,))
            while cursor.nextset() is not None:
                pass
            cursor.execute('CREATE SCHEMA %s' % (schema_name,))
            while cursor.nextset() is not None:
                pass
            msg = "Database schema '%s' was created." % (schema_name,)
            log.info(msg)
            self._store_message(msg)
        conn.close()

        with transaction.commit_on_success():

            # delete existing results
            models.ChangesetTest.objects.filter(
                changeset_detail__changeset=self._changeset).delete()

            #
            # reconnect using the newly created schema
            #
            connection_options = self._connection_options.copy()
            connection_options['db'] = schema_name
            conn = MySQLdb.connect(**connection_options)

            try:
                #
                # load initial schema
                #
                ddls = sqlparse.split(self._schema_version.ddl)
                for ddl in ddls:
                    cursor = None
                    try:
                        ddl = ddl.rstrip(unicode(string.whitespace + ';'))
                        log.debug(ddl)
                        cursor = conn.cursor()
                        if ddl:
                            cursor.execute(ddl)
                    finally:
                        if cursor:
                            while cursor.nextset() is not None:
                                pass
                        cursor.close()

                #
                # Apply all changeset details.
                #
                first_run = True
                for changeset_detail in (
                        self._changeset.changeset_details.select_related()
                            .order_by('id')):
                    if first_run:
                        # initial before structure and checksum should be the
                        # same with schema version
                        structure_before = self._schema_version.ddl
                        hash_before = self._schema_version.checksum
                        structure_after = structure_before
                        hash_after = hash_before
                        first_run = False
                        log.debug('Structure=\n%s\nChecksum=%s' % (
                            structure_before, hash_before))
                    else:
                        # for succeeding runs, before structure and checksum
                        # is equal to after structure and checksum of the
                        # preceeding operation
                        structure_before = structure_after
                        hash_before = hash_after
                        structure_after = structure_before
                        hash_after = hash_before

                    self._structure_after = structure_after
                    self._hash_after = hash_after

                    msg = u'Testing changeset detail...\nid: %s\napply_sql:\n%s' % (
                        changeset_detail.id, changeset_detail.apply_sql)
                    log.info(msg)
                    self._store_message(msg)

                    started_at = timezone.now()
                    cursor = None
                    results_log_items = []
                    try:
                        cursor = conn.cursor()

                        count_before = self._execute_count_sql(
                            cursor, changeset_detail.count_sql)
                        log.debug('Row count before apply_sql: %s' % (
                            count_before,))

                        # Test apply_sql
                        log.debug('Testing apply_sql')
                        self._execute_query(cursor, changeset_detail.apply_sql)
                        structure_after = utils.mysql_dump(**connection_options)
                        hash_after = utils.schema_hash(structure_after)
                        log.debug('Structure=\n%s\nChecksum=%s' % (
                            structure_after, hash_after))

                        count_after = self._execute_count_sql(
                            cursor, changeset_detail.count_sql)
                        log.debug('Row count after apply_sql: %s' % (
                            count_after,))

                        # Test revert_sql
                        log.debug('Testing revert_sql')
                        self._execute_query(cursor, changeset_detail.revert_sql)
                        structure_after_revert = utils.mysql_dump(
                            **connection_options)
                        hash_after_revert = utils.schema_hash(
                            structure_after_revert)
                        if hash_after_revert != hash_before:
                            raise exceptions.Error(
                                'Checksum after revert_sql was applied was '
                                'not the same as before apply_sql was '
                                'applied.')

                        test_count = self._execute_count_sql(
                            cursor, changeset_detail.count_sql)
                        log.debug('Row count after revert_sql: %s' % (
                            test_count,))
                        if test_count != count_before:
                            raise exceptions.Error(
                                'Row count after revert_sql does not match '
                                'the count before apply_sql was applied.')

                        # revert_sql worked, reapply appy sql again
                        log.debug('Reapplying apply_sql')
                        self._execute_query(cursor, changeset_detail.apply_sql)

                        test_count = self._execute_count_sql(
                            cursor, changeset_detail.count_sql)
                        log.debug('Row count after reapplying apply_sql: %s' % (
                            test_count,))
                        if test_count != count_after:
                            raise exceptions.Error(
                                'Row count after apply_sql was reapplied '
                                'was different from expected value.')

                        #ddls = sqlparse.split(changeset_detail.apply_sql)
                        #for ddl in ddls:
                        #    ddl = ddl.rstrip(unicode(string.whitespace + ';'))
                        #    if ddl:
                        #        tmp_ddl = ddl.strip().lower()
                        #        if not (
                        #                tmp_ddl.startswith('insert') or
                        #                tmp_ddl.startswith('update') or
                        #                tmp_ddl.startswith('del')):
                        #            log.debug(ddl)
                        #            cursor.execute(ddl)
                        #            while cursor.nextset() is not None:
                        #                pass

                        changeset_detail.before_checksum = hash_before
                        changeset_detail.after_checksum = hash_after
                        if (
                                count_before is not None and
                                count_after is not None):
                            changeset_detail.volumetric_values = (
                                u'%s' % (count_after - count_before))
                        changeset_detail.save()

                        self._structure_after = structure_after
                        self._hash_after = hash_after
                    except Exception, e:
                        msg = 'ERROR %s: %s' % (type(e), e)
                        log.exception(msg)
                        self._store_message(msg, 'error')
                        if cursor and cursor.messages:
                            log.error(cursor.messages)
                            for exc, val in cursor.messages:
                                val_str = 'ERROR %s: %s' % (exc, val)
                                if val_str not in results_log_items:
                                    results_log_items.append(val_str)
                        else:
                            results_log_items.append(msg)
                        self._has_errors = True
                    finally:
                        if cursor:
                            while cursor.nextset() is not None:
                                pass
                            cursor.close()

                    ended_at = timezone.now()
                    results_log = u'\n'.join(results_log_items)
                    test_type = models.TestType.objects.get_syntax_test_type()
                    changeset_test = models.ChangesetTest.objects.create(
                        changeset_detail=changeset_detail,
                        test_type=test_type,
                        started_at=started_at,
                        ended_at=ended_at,
                        results_log=results_log)
                    self._changeset_tests.append(changeset_test)

            except Exception, e:
                log.exception('EXCEPTION')
                self._store_message('EXCEPTION %s: %s' % (type(e), e), 'error')
                self._has_errors = True

            finally:
                conn.close()

        msg = 'Changeset syntax test was completed.'
        log.info(msg)
        self._store_message(msg)
