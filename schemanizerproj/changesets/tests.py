import logging

from django.conf import settings
from django.test import TestCase

import MySQLdb

from users import models as users_models
from schemaversions import schema_functions
from servers import models as servers_models
from . import changeset_functions, models

log = logging.getLogger(__name__)


class SubmitChangesetTestCase(TestCase):

    fixtures = ['schemanizer/test.json']

    def setUp(self):
        self.user_admin = users_models.User.objects.get(name='admin')
        self.user_dba01 = users_models.User.objects.get(name='dba01')
        self.user_dba02 = users_models.User.objects.get(name='dba02')
        self.user_dev01 = users_models.User.objects.get(name='dev01')
        self.user_dev02 = users_models.User.objects.get(name='dev02')


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

    def test_submit_changeset(self):

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

        print 'schema_version = %s' % self.schema_version
        print 'schema_version.database_schema = %s' % self.schema_version.database_schema

        changeset = models.Changeset(
            database_schema=self.schema_version.database_schema,
            type=models.Changeset.DDL_TABLE_CREATE,
            classification=models.Changeset.CLASSIFICATION_PAINLESS,
        )

        changeset_detail = models.ChangesetDetail(
            description = 'create table t01',
            apply_sql = 'create table t01 (id int)',
            revert_sql = 'drop table t01'
        )

        changeset = changeset_functions.submit_changeset(
            from_form=False, submitted_by=self.user_dev01,
            changeset=changeset,
            changeset_detail_list=[changeset_detail],
            unit_testing=True)

        print 'changeset = %s' % changeset

        self.assertTrue(changeset.pk is not None)
        self.assertEqual(changeset.submitted_by, self.user_dev01)
        self.assertTrue(changeset.submitted_at is not None)
