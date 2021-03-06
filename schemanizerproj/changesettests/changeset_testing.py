import logging
import string
import MySQLdb
from django.utils import timezone
import sqlparse
from changesettests import models as changesettests_models
from utils import mysql_functions, exceptions
from . import models

log = logging.getLogger(__name__)


class ChangesetTestSyntax(object):
    def __init__(self, changeset, **kwargs):
        super(ChangesetTestSyntax, self).__init__()

        self.test_type = models.TestType.objects.get(name='syntax')
        self.changeset = changeset
        self.schema_version = kwargs.get('schema_version')
        self.connection_options = kwargs.get('connection_options')
        self.message_callback = kwargs.get('message_callback')

        self.test_log = []

        self.messages = []
        self.changeset_tests = []
        self.has_errors = False
        self.structure_after = None
        self.hash_after = None

        assert(
            self.changeset.database_schema.id ==
            self.schema_version.database_schema.id)

    def store_message(self, message, message_type='info'):
        """Stores message."""
        self.messages.append(dict(
            message=message,
            message_type=message_type))
        if self.message_callback:
            self.message_callback(message, message_type)

    def execute_query(self, cursor, query):
        """Executes query."""
        statements = sqlparse.split(query)
        for statement in statements:
            statement = statement.rstrip(unicode(string.whitespace + ';'))
            if statement:
                cursor.execute(statement)
                while cursor.nextset() is not None:
                    pass

    def run_test(self):
        """Main logic for testing changeset."""

        msg = (
            'Changeset syntax test started.\n'
            'Testing against SchemaVersion: id=%s' % self.schema_version.pk)
        log.info(msg)
        self.store_message(msg)

        log.debug('Changeset: id=%s', self.changeset.pk)

        schema_name = self.changeset.database_schema.name
        conn = MySQLdb.connect(**self.connection_options)
        cursor = None
        try:
            cursor = conn.cursor()

            #
            # Create schema.
            #
            try:
                sql = 'DROP SCHEMA IF EXISTS %s' % schema_name
                log.debug('Executing: %s', sql)
                cursor.execute(sql)
            except Warning, e:
                log.warn('EXCEPTION %s: %s' % (type(e), e))
                # ignore warnings
                pass
            while cursor.nextset() is not None:
                pass
            sql = 'CREATE SCHEMA %s' % schema_name
            log.debug('Executing: %s', sql)
            cursor.execute(sql)
            while cursor.nextset() is not None:
                pass
            msg = "Database schema '%s' was created." % (schema_name,)
            log.info(msg)
            self.store_message(msg)

            #
            # Connect to newly created schema.
            #
            sql = 'USE %s' % schema_name
            log.debug('Executing: %s', sql)
            cursor.execute(sql)

            dump_connection_options = self.connection_options.copy()
            dump_connection_options['db'] = schema_name

            #
            # Load initial schema.
            #
            log.debug(
                'Loading initial schema:\n%s',
                self.schema_version.ddl)
            ddls = sqlparse.split(self.schema_version.ddl)
            for ddl in ddls:
                try:
                    ddl = ddl.rstrip(unicode(string.whitespace + ';'))
                    if ddl:
                        cursor.execute(ddl)
                finally:
                    while cursor.nextset() is not None:
                        pass

            #
            # Delete existing results.
            #
            changesettests_models.ChangesetTest.objects.filter(
                changeset_detail__changeset=self.changeset).delete()
            log.debug('Existing test results deleted.')

            #
            # Apply all changeset details.
            #
            structure_after = ''
            hash_after = ''
            first_run = True
            for changeset_detail in (
                    self.changeset.changesetdetail_set.select_related()
                        .order_by('id')):

                msg = u'Testing ChangesetDetail: id=%s' % changeset_detail.pk
                log.info(msg)
                self.store_message(msg)

                if first_run:
                    log.debug('first_run=%s', first_run)

                    #
                    # Initial before structure and checksum should be the
                    # same with schema version.
                    #
                    structure_before = self.schema_version.ddl
                    hash_before = self.schema_version.checksum
                    structure_after = structure_before
                    hash_after = hash_before
                    first_run = False
                else:
                    #
                    # For succeeding runs, before structure and checksum
                    # is equal to after structure and checksum of the
                    # preceeding operation.
                    #
                    structure_before = structure_after
                    hash_before = hash_after
                    structure_after = structure_before
                    hash_after = hash_before

                #
                # Track final structure after applying changes.
                #
                self.structure_after = structure_after
                self.hash_after = hash_after


                started_at = timezone.now()
                results_log_items = []
                try:

                    #
                    # Execute apply_sql
                    #
                    msg = u'Executing apply_sql:\n%s' % changeset_detail.apply_sql
                    log.info(msg)
                    self.store_message(msg)
                    self.execute_query(cursor, changeset_detail.apply_sql)
                    cursor.execute('FLUSH TABLES')

                    #
                    # Track resulting schema after executing apply_sql.
                    #
                    structure_after = mysql_functions.dump_schema(
                        **dump_connection_options)
                    hash_after = mysql_functions.generate_schema_hash(
                        structure_after)
                    log.debug(
                        'Resulting schema:\nStructure=\n%s\nChecksum=%s',
                        structure_after, hash_after)

                    #
                    # Execute apply_verification_sql
                    #
                    try:
                        if changeset_detail.apply_verification_sql:
                            log.debug(
                                'Executing apply_verification_sql:\n%s',
                                changeset_detail.apply_verification_sql)
                            self.execute_query(
                                cursor,
                                changeset_detail.apply_verification_sql)
                    except Exception, e:
                        msg = (
                            u'Apply verification failed (Error %s: %s).' % (
                                type(e), e))
                        raise exceptions.Error(msg)

                    #
                    # Execute revert_sql
                    #
                    log.debug(
                        u'Executing revert_sql:\n%s',
                        changeset_detail.revert_sql)
                    self.execute_query(cursor, changeset_detail.revert_sql)
                    cursor.execute('FLUSH TABLES')

                    #
                    # Check if revert_sql has resulted to the original
                    # schema before apply_sql was applied.
                    #
                    structure_after_revert = mysql_functions.dump_schema(
                        **dump_connection_options)
                    hash_after_revert = mysql_functions.generate_schema_hash(
                        structure_after_revert)
                    if hash_after_revert != hash_before:
                        raise exceptions.Error(
                            'Checksum after revert_sql was applied was '
                            'not the same as before apply_sql was '
                            'applied.')


                    #
                    # Execute revert_verification_sql
                    #
                    try:
                        if changeset_detail.revert_verification_sql:
                            log.debug(
                                'Executing revert_verification_sql: \n%s',
                                changeset_detail.revert_verification_sql)
                            self.execute_query(
                                cursor,
                                changeset_detail.revert_verification_sql)
                    except Exception, e:
                        msg = (
                            u'Revert verification failed (Error %s: %s).' % (
                                type(e), e))
                        raise exceptions.Error(msg)

                    #
                    # revert_sql worked, finalize change by reapplying
                    # apply_sql
                    #
                    log.debug('Reapplying apply_sql.')
                    self.execute_query(cursor, changeset_detail.apply_sql)

                    #
                    # Update changeset_detail with info on schema versions.
                    #
                    changeset_detail.before_checksum = hash_before
                    changeset_detail.after_checksum = hash_after
                    changeset_detail.save()

                    #
                    # Remember the last schema changes
                    #
                    self.structure_after = structure_after
                    self.hash_after = hash_after

                except Exception, e:
                    msg = 'ERROR %s: %s' % (type(e), e)
                    log.exception(msg)
                    self.store_message(msg, 'error')
                    results_log_items.append(msg)
                    self.has_errors = True

                finally:
                    while cursor.nextset() is not None:
                        pass

                #
                # Save test result.
                #
                ended_at = timezone.now()
                results_log = u'\n'.join(results_log_items)
                test_type =  self.test_type
                changeset_test = changesettests_models.ChangesetTest.objects.create(
                    changeset_detail=changeset_detail,
                    test_type=test_type,
                    started_at=started_at,
                    ended_at=ended_at,
                    results_log=results_log)
                log.debug('Created ChangesetTest: id=%s', changeset_test.pk)

                # Collect changeset test results
                self.changeset_tests.append(changeset_test)

        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            log.exception(msg)
            self.store_message(msg, 'error')
            self.has_errors = True
            raise e

        finally:
            if cursor:
                try:
                    cursor.execute('FLUSH TABLES')
                except Exception, e:
                    msg = 'ERROR %s: %s' % (type(e), e)
                    log.exception(msg)
                    self.store_message(msg, 'error')
                    self.has_errors = True

                while cursor.nextset() is not None:
                    pass
            conn.close()

        msg = 'Changeset syntax test ended.'
        log.info(msg)
        self.store_message(msg)

        return dict(
            structure_after=self.structure_after,
            hash_after=self.hash_after,
            changeset_tests=self.changeset_tests,
            has_errors=self.has_errors,
        )


test_map = {
    'syntax': ChangesetTestSyntax,
}


def run_tests(changeset, **kwargs):
    test_types = models.TestType.objects.all()
    test_results = {}
    for test_type in test_types:
        if test_type.name in test_map:
            klass = test_map[test_type.name]
            instance = klass(changeset, **kwargs)
            test_results[test_type.name] = instance.run_test()
    return test_results


# class ChangesetSyntaxTest(object):
#     """Contains changeset syntax test logic."""
#
#     def __init__(
#             self, changeset, schema_version, connection_options=None,
#             message_callback=None):
#         """Initializes object."""
#
#         super(ChangesetSyntaxTest, self).__init__()
#
#         self._changeset = changeset
#         self._schema_version = schema_version
#         self._connection_options = connection_options
#         self._message_callback = message_callback
#
#         self._init_run_vars()
#
#     def _init_run_vars(self):
#         """Initializes variables used when running logic."""
#         self._messages = []
#         self._changeset_tests = []
#         self._has_errors = False
#         self._structure_after = None
#         self._hash_after = None
#
#     @property
#     def messages(self):
#         """Returns messages."""
#         return self._messages
#
#     @property
#     def changeset_tests(self):
#         """Returns changeset test results."""
#         return self._changeset_tests
#
#     @property
#     def has_errors(self):
#         """Returns True if test has errors, otherwise False."""
#         return self._has_errors
#
#     @property
#     def structure_after(self):
#         """Returns structure after tests are performed."""
#         return self._structure_after
#
#     @property
#     def hash_after(self):
#         """Returns hash of structure after tests are performed."""
#         return self._hash_after
#
#     def _store_message(self, message, message_type='info'):
#         """Stores message."""
#         self._messages.append(dict(
#             message=message,
#             message_type=message_type))
#         if self._message_callback:
#             self._message_callback(message, message_type)
#
#     def _execute_query(self, cursor, query):
#         """Executes query."""
#         statements = sqlparse.split(query)
#         for statement in statements:
#             statement = statement.rstrip(unicode(string.whitespace + ';'))
#             if statement:
#                 log.debug(statement)
#                 cursor.execute(statement)
#                 while cursor.nextset() is not None:
#                     pass
#
#     def run(self):
#         """Main logic for testing changeset."""
#
#         self._init_run_vars()
#
#         if (self._changeset.database_schema_id !=
#                 self._schema_version.database_schema_id):
#             log.debug('self._changeset.id = %s' % (self._changeset.id,))
#             log.debug('self._schema_version.id = %s' % (self._schema_version.id,))
#             msg = 'Schema version and changeset do have the same database schema.'
#             log.error(msg)
#             self._store_message(msg, 'error')
#             self._has_errors = True
#             return
#
#         msg = 'Changeset syntax test was started.'
#         log.info(msg)
#         self._store_message(msg)
#
#         schema_name = self._changeset.database_schema.name
#         conn = MySQLdb.connect(**self._connection_options)
#         cursor = None
#         try:
#             cursor = conn.cursor()
#             #
#             # Create schema
#             #
#             try:
#                 cursor.execute('DROP SCHEMA IF EXISTS %s' % (schema_name,))
#             except Warning, e:
#                 log.warn('EXCEPTION %s: %s' % (type(e), e))
#                 # ignore warnings
#                 pass
#             while cursor.nextset() is not None:
#                 pass
#             cursor.execute('CREATE SCHEMA %s' % (schema_name,))
#             while cursor.nextset() is not None:
#                 pass
#             msg = "Database schema '%s' was created." % (schema_name,)
#             log.info(msg)
#             self._store_message(msg)
#             #
#             # connect to newly created schema
#             cursor.execute('USE %s' % (schema_name,))
#
#             dump_connection_options = self._connection_options.copy()
#             dump_connection_options['db'] = schema_name
#
#             #
#             # load initial schema
#             #
#             log.debug('Initial schema:\n%s' % (self._schema_version.ddl,))
#             ddls = sqlparse.split(self._schema_version.ddl)
#             for ddl in ddls:
#                 try:
#                     ddl = ddl.rstrip(unicode(string.whitespace + ';'))
#                     if ddl:
#                         cursor.execute(ddl)
#                 finally:
#                     while cursor.nextset() is not None:
#                         pass
#
#             # delete existing results
#             ChangesetTest.objects.filter(
#                 changeset_detail__changeset=self._changeset).delete()
#
#             #
#             # Apply all changeset details.
#             #
#             first_run = True
#             for changeset_detail in (
#                     self._changeset.changeset_details.select_related()
#                         .order_by('id')):
#                 if first_run:
#                     # initial before structure and checksum should be the
#                     # same with schema version
#                     structure_before = self._schema_version.ddl
#                     hash_before = self._schema_version.checksum
#                     structure_after = structure_before
#                     hash_after = hash_before
#                     first_run = False
#                     log.debug('Structure=\n%s\nChecksum=%s' % (
#                         structure_before, hash_before))
#                 else:
#                     # for succeeding runs, before structure and checksum
#                     # is equal to after structure and checksum of the
#                     # preceeding operation
#                     structure_before = structure_after
#                     hash_before = hash_after
#                     structure_after = structure_before
#                     hash_after = hash_before
#
#                 self._structure_after = structure_after
#                 self._hash_after = hash_after
#
#                 msg = u'Testing changeset detail...\nid: %s\napply_sql:\n%s' % (
#                     changeset_detail.id, changeset_detail.apply_sql)
#                 log.info(msg)
#                 self._store_message(msg)
#
#                 started_at = timezone.now()
#                 results_log_items = []
#                 try:
#                     # counts_before = utils.execute_count_statements(
#                     #     cursor, changeset_detail.apply_verification_sql)
#                     # log.debug('Row count(s) before apply_sql: %s' % (
#                     #     counts_before,))
#
#                     # Test apply_sql
#                     log.debug('Testing apply_sql')
#                     self._execute_query(cursor, changeset_detail.apply_sql)
#                     cursor.execute('FLUSH TABLES')
#
#                     structure_after = mysql_dump(
#                         **dump_connection_options)
#                     hash_after = generate_schema_hash(structure_after)
#                     log.debug('Structure=\n%s\nChecksum=%s' % (
#                         structure_after, hash_after))
#
#                     # counts_after = utils.execute_count_statements(
#                     #     cursor, changeset_detail.apply_verification_sql)
#                     # log.debug('Row count(s) after apply_sql: %s' % (
#                     #     counts_after,))
#
#                     try:
#                         if changeset_detail.apply_verification_sql:
#                             self._execute_query(
#                                 cursor,
#                                 changeset_detail.apply_verification_sql)
#                     except Exception, e:
#                         msg = (
#                             u'Apply verification failed (Error %s: %s).' % (
#                                 type(e), e))
#                         raise Error(msg)
#
#                     # Test revert_sql
#                     log.debug('Testing revert_sql')
#                     self._execute_query(cursor, changeset_detail.revert_sql)
#                     cursor.execute('FLUSH TABLES')
#
#                     structure_after_revert = mysql_dump(
#                         **dump_connection_options)
#                     hash_after_revert = generate_schema_hash(
#                         structure_after_revert)
#                     if hash_after_revert != hash_before:
#                         raise Error(
#                             'Checksum after revert_sql was applied was '
#                             'not the same as before apply_sql was '
#                             'applied.')
#
#                     try:
#                         if changeset_detail.revert_verification_sql:
#                             self._execute_query(
#                                 cursor,
#                                 changeset_detail.revert_verification_sql)
#                     except Exception, e:
#                         msg = (
#                             u'Revert verification failed (Error %s: %s).' % (
#                                 type(e), e))
#                         raise Error(msg)
#
#                     # test_counts = utils.execute_count_statements(
#                     #     cursor, changeset_detail.apply_verification_sql)
#                     # log.debug('Row count(s) after revert_sql: %s' % (
#                     #     test_counts,))
#                     # if test_counts != counts_before:
#                     #     raise exceptions.Error(
#                     #         'Count SQL result after revert_sql does not '
#                     #         'match the result before apply_sql was '
#                     #         'applied.')
#
#                     # revert_sql worked, reapply appy sql again
#                     log.debug('Reapplying apply_sql')
#                     self._execute_query(cursor, changeset_detail.apply_sql)
#
#                     # test_counts = utils.execute_count_statements(
#                     #     cursor, changeset_detail.apply_verification_sql)
#                     # log.debug('Row count(s) after reapplying apply_sql: %s' % (
#                     #     test_counts,))
#                     # if test_counts != counts_after:
#                     #     raise exceptions.Error(
#                     #         'Count SQL result after apply_sql was reapplied '
#                     #         'was different from expected value.')
#
#                     changeset_detail.before_checksum = hash_before
#                     changeset_detail.after_checksum = hash_after
#                     # changeset_detail.volumetric_values = u','.join(
#                     #     itertools.imap(
#                     #         lambda before, after:
#                     #             unicode(after - before)
#                     #             if (before is not None and after is not None)
#                     #             else '',
#                     #         counts_before, counts_after))
#                     changeset_detail.save()
#
#                     self._structure_after = structure_after
#                     self._hash_after = hash_after
#                 except Exception, e:
#                     msg = 'ERROR %s: %s' % (type(e), e)
#                     log.exception(msg)
#                     self._store_message(msg, 'error')
#                     # if cursor.messages:
#                     #     log.error(cursor.messages)
#                     #     for exc, val in cursor.messages:
#                     #         val_str = 'ERROR %s: %s' % (exc, val)
#                     #         if val_str not in results_log_items:
#                     #             results_log_items.append(val_str)
#                     # else:
#                     results_log_items.append(msg)
#                     self._has_errors = True
#                 finally:
#                     while cursor.nextset() is not None:
#                         pass
#
#                 ended_at = timezone.now()
#                 results_log = u'\n'.join(results_log_items)
#                 test_type = TestType.objects.get_syntax_test_type()
#                 changeset_test = ChangesetTest.objects.create(
#                     changeset_detail=changeset_detail,
#                     test_type=test_type,
#                     started_at=started_at,
#                     ended_at=ended_at,
#                     results_log=results_log)
#                 self._changeset_tests.append(changeset_test)
#
#         except Exception, e:
#             msg = 'ERROR %s: %s' % (type(e), e)
#             log.exception(msg)
#             self._store_message(msg, 'error')
#             self._has_errors = True
#             raise e
#
#         finally:
#             if cursor:
#                 try:
#                     cursor.execute('FLUSH TABLES')
#                 except Exception, e:
#                     msg = 'ERROR %s: %s' % (type(e), e)
#                     log.exception(msg)
#                     self._store_message(msg, 'error')
#                     self._has_errors = True
#
#                 while cursor.nextset() is not None:
#                     pass
#             conn.close()
#
#         msg = 'Changeset syntax test was completed.'
#         log.info(msg)
#         self._store_message(msg)