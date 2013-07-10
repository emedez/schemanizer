import logging

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

import MySQLdb

from changesetreviews import changeset_review
from changesets import models as changesets_models
from schemaversions import schema_functions
from servers import models as servers_models
from users import models as users_models
from . import changeset_apply, models

log = logging.getLogger(__name__)


class ChangesetApplyTestCase(TestCase):

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

    def test_apply_changeset(self):
        changeset = changesets_models.Changeset.objects.create(
            database_schema=self.schema_version.database_schema,
            type=changesets_models.Changeset.DDL_TABLE_CREATE,
            classification=changesets_models.Changeset.CLASSIFICATION_PAINLESS,
            review_status=changesets_models.Changeset.REVIEW_STATUS_APPROVED,
        )
        changeset_detail = changesets_models.ChangesetDetail.objects.create(
            changeset=changeset,
            description='create table t01',
            apply_sql='create table t01 (id int)',
            revert_sql='drop table t01'
        )

        changeset_apply_class_instance = changeset_apply.apply_changeset(
            changeset=changeset,
            applied_by=self.user_dba01,
            server=self.server_test,
            unit_testing=True
        )
        changeset_apply_obj = changeset_apply_class_instance.changeset_apply

        self.assertTrue(changeset_apply_obj.success)


class ChangesetAlreadyAppliedTestCase(TestCase):
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

    def test_apply_changeset_already_applied(self):
        changeset = changesets_models.Changeset.objects.create(
            database_schema=self.schema_version.database_schema,
            type=changesets_models.Changeset.DDL_TABLE_CREATE,
            classification=changesets_models.Changeset.CLASSIFICATION_PAINLESS,
            review_status=changesets_models.Changeset.REVIEW_STATUS_APPROVED,
        )
        changeset_detail = changesets_models.ChangesetDetail.objects.create(
            changeset=changeset,
            description='create table t01',
            apply_sql='create table t01 (id int)',
            revert_sql='drop table t01'
        )

        # simulate an applied changeset
        changeset_apply_obj = models.ChangesetApply.objects.create(
            changeset=changeset, server=self.server_test,
            applied_at=timezone.now(), applied_by=self.user_dba01,
            success=True,
            changeset_action=changesets_models.ChangesetAction.objects.create(
                changeset=changeset,
                type=changesets_models.ChangesetAction.TYPE_APPLIED,
                timestamp=timezone.now()
            )
        )

        changeset_apply_class_instance = changeset_apply.apply_changeset(
            changeset=changeset,
            applied_by=self.user_dba01,
            server=self.server_test,
            unit_testing=True
        )
        changeset_apply_obj = changeset_apply_class_instance.changeset_apply

        self.assertTrue(not changeset_apply_obj.success)


class ChangesetApplyIncorrectInitialSchemaTestCase(TestCase):
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

    def test_apply_changeset_incorrect_initial_schema(self):
        changeset = changesets_models.Changeset.objects.create(
            database_schema=self.schema_version.database_schema,
            type=changesets_models.Changeset.DDL_TABLE_CREATE,
            classification=changesets_models.Changeset.CLASSIFICATION_PAINLESS,
        )
        changeset_detail = changesets_models.ChangesetDetail.objects.create(
            changeset=changeset,
            description='create table t01',
            apply_sql='create table t01 (id int)',
            revert_sql='drop table t01'
        )

        # simulate changeset review
        changeset_review_class_instance = changeset_review.review_changeset(
            changeset, self.schema_version, reviewed_by=self.user_dba01,
            unit_testing=True
        )
        changeset_review_obj = changeset_review_class_instance.changeset_review
        self.assertTrue(changeset_review_obj.success)

        # approved changeset simulation
        changeset = changesets_models.Changeset.objects.get(pk=changeset.pk)
        changeset.review_status = changesets_models.Changeset.REVIEW_STATUS_APPROVED
        changeset.save()

        changeset_apply_class_instance = changeset_apply.apply_changeset(
            changeset, self.user_dba01, self.server_test,
            unit_testing=True
        )
        changeset_apply_obj = changeset_apply_class_instance.changeset_apply
        self.assertTrue(changeset_apply_obj.success)

        # delete changeset_apply object so that we could perform
        # changeset apply again, this time that target db has already changed
        # due to the first apply performed, the next apply should encounter
        # incorrect initial schema and thus fail
        changeset_apply_obj.delete()
        changeset_apply_class_instance = changeset_apply.apply_changeset(
            changeset, self.user_dba01, self.server_test,
            unit_testing=True
        )
        changeset_apply_obj = changeset_apply_class_instance.changeset_apply
        self.assertTrue(not changeset_apply_obj.success)
