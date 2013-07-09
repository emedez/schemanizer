import logging

from django.conf import settings
from django.test import TestCase

import MySQLdb

from changesets import models as changesets_models
from schemaversions import schema_functions
from servers import models as servers_models
from users import models as users_models
from . import changeset_testing, models

log = logging.getLogger(__name__)


class ChangesetTestSyntaxTestCase(TestCase):

    fixtures = ['schemanizer/test.json']

    def setUp(self):
        self.user_admin = users_models.User.objects.get(name='admin')
        self.user_dba01 = users_models.User.objects.get(name='dba01')
        self.user_dba02 = users_models.User.objects.get(name='dba02')
        self.user_dev01 = users_models.User.objects.get(name='dev01')
        self.user_dev02 = users_models.User.objects.get(name='dev02')

        self.create_test_db()

        self.server_test = servers_models.Server.objects.create(
            name='test',
            hostname=settings.TEST_DB_HOST if settings.TEST_DB_HOST else 'localhost',
            environment=servers_models.Environment.objects.get(name='test'))

        conn_opts = self.get_test_db_connection_options()
        self.schema_version, created = schema_functions.generate_schema_version(
            self.server_test, settings.TEST_DB_NAME,
            connection_options=conn_opts
        )

    def get_test_db_connection_options(self):
        conn_opts = {}
        if settings.TEST_DB_HOST:
            conn_opts['host'] = settings.TEST_DB_HOST
        if settings.TEST_DB_PORT:
            conn_opts['port'] = settings.TEST_DB_PORT
        if settings.TEST_DB_USER:
            conn_opts['user'] = settings.TEST_DB_USER
        if settings.TEST_DB_PASSWORD:
            conn_opts['passwd'] = settings.TEST_DB_PASSWORD
        return conn_opts

    def get_syntax_test_connection_coptions(self):
        conn_opts = {}
        if settings.MYSQL_HOST:
            conn_opts['host'] = settings.MYSQL_HOST
        if settings.MYSQL_PORT:
            conn_opts['port'] = settings.MYSQL_PORT
        if settings.MYSQL_USER:
            conn_opts['user'] = settings.MYSQL_USER
        if settings.MYSQL_PASSWORD:
            conn_opts['passwd'] = settings.MYSQL_PASSWORD
        return conn_opts

    def create_test_db(self):
        conn = MySQLdb.connect(**self.get_test_db_connection_options())
        with conn as cursor:
            try:
                cursor.execute(
                    'DROP SCHEMA IF EXISTS %s' % settings.TEST_DB_NAME)
            except MySQLdb.Warning:
                # ignore warnings
                pass
            cursor.execute('CREATE SCHEMA %s' % settings.TEST_DB_NAME)
        conn.close()

    def test_syntax_test_changeset(self):
        changeset = changesets_models.Changeset.objects.create(
            database_schema=self.schema_version.database_schema,
            type=changesets_models.Changeset.DDL_TABLE_CREATE,
            classification=changesets_models.Changeset.CLASSIFICATION_PAINLESS
        )
        changeset_detail = changesets_models.ChangesetDetail.objects.create(
            changeset=changeset,
            description='create table t01',
            apply_sql='create table t01 (id int)',
            revert_sql='drop table t01'
        )

        changeset_test_syntax = changeset_testing.ChangesetTestSyntax(
            changeset=changeset,
            schema_version=self.schema_version,
            connection_options=self.get_syntax_test_connection_coptions()
        )
        changeset_test_syntax.run_test()

        changeset_tests = models.ChangesetTest.objects.filter(
            changeset_detail=changeset_detail
        )

        self.assertTrue(changeset_tests.exists())
        self.assertFalse(changeset_test_syntax.has_errors)

    def test_syntax_test_changeset_with_errors_on_apply_sql(self):
        changeset = changesets_models.Changeset.objects.create(
            database_schema=self.schema_version.database_schema,
            type=changesets_models.Changeset.DDL_TABLE_CREATE,
            classification=changesets_models.Changeset.CLASSIFICATION_PAINLESS
        )
        changeset_detail = changesets_models.ChangesetDetail.objects.create(
            changeset=changeset,
            description='create table t01',
            apply_sql='createee table t01 (id int)',
            revert_sql='drop table t01'
        )

        changeset_test_syntax = changeset_testing.ChangesetTestSyntax(
            changeset=changeset,
            schema_version=self.schema_version,
            connection_options=self.get_syntax_test_connection_coptions()
        )
        changeset_test_syntax.run_test()

        changeset_tests = models.ChangesetTest.objects.filter(
            changeset_detail=changeset_detail
        )

        self.assertTrue(changeset_tests.exists())
        self.assertTrue(changeset_test_syntax.has_errors)

    def test_syntax_test_changeset_with_errors_on_revert_sql(self):
        changeset = changesets_models.Changeset.objects.create(
            database_schema=self.schema_version.database_schema,
            type=changesets_models.Changeset.DDL_TABLE_CREATE,
            classification=changesets_models.Changeset.CLASSIFICATION_PAINLESS
        )
        changeset_detail = changesets_models.ChangesetDetail.objects.create(
            changeset=changeset,
            description='create table t01',
            apply_sql='create table t01 (id int)',
            revert_sql='ddrop table t01'
        )

        changeset_test_syntax = changeset_testing.ChangesetTestSyntax(
            changeset=changeset,
            schema_version=self.schema_version,
            connection_options=self.get_syntax_test_connection_coptions()
        )
        changeset_test_syntax.run_test()

        changeset_tests = models.ChangesetTest.objects.filter(
            changeset_detail=changeset_detail
        )

        self.assertTrue(changeset_tests.exists())
        self.assertTrue(changeset_test_syntax.has_errors)
