"""ChangesetApply tests."""

import logging

from django.conf import settings
from django.test import TestCase
from django.test.utils import override_settings
from django.utils import timezone

import MySQLdb

from schemanizer import models, utils
from schemanizer.logic import changeset_apply as changeset_apply_logic
from schemanizer.logic import changeset_review as changeset_review_logic

log = logging.getLogger(__name__)


class ChangesetApplyTest(TestCase):
    """Tests for ChangesetApply."""

    fixtures = ['schemanizer/test.yaml']

    def create_approved_changeset(
            self, database_schema, submitted_by, approved_by):
        changeset = models.Changeset.objects.create(
            database_schema=database_schema,
            type=models.Changeset.DDL_TABLE_CREATE,
            classification=models.Changeset.CLASSIFICATION_PAINLESS,
            submitted_by=submitted_by,
            submitted_at=timezone.now(),
            approved_by=approved_by,
            approved_at=timezone.now()
        )

        models.ChangesetDetail.objects.create(
            changeset=changeset,
            type=models.ChangesetDetail.TYPE_ADD,
            description='Add people table.',
            apply_sql="""
                CREATE TABLE people (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(255),
                    email VARCHAR(255),
                    dept VARCHAR(255)) ENGINE=InnoDB DEFAULT CHARSET=utf8;
                """,
            revert_sql='DROP TABLE people',
        )

        models.ChangesetDetail.objects.create(
            changeset=changeset,
            type=models.ChangesetDetail.TYPE_INS,
            description='Insert people rows.',
            apply_sql="""
                INSERT INTO people
                VALUES
                    (1, 'moss', 'moss@example.com', 'tools'),
                    (2, 'rod', 'rod@example.com', 'tools'),
                    (3, 'laine', 'laine@example.com', 'leadership'),
                    (4, 'charlie', 'charlie@example.com', 'leardership'),
                    (5, 'jay', 'jay@example.com', 'leadership')
                """,
            revert_sql="""
                DELETE FROM people
                WHERE id in (1, 2, 3, 4, 5)
                """,
            count_sql="""
                SELECT COUNT(*) FROM people
                WHERE dept='tools' AND id IN (1, 2);
                SELECT COUNT(*) FROM people
                WHERE dept='leadership' AND id IN (3, 4, 5);
                SELECT COUNT(*) FROM people
                WHERE id IN (1, 2, 3, 4, 5)
                """
        )

        return changeset

    def setUp(self):
        # delete (if exists) and create database schema
        no_db_connect_args = dict(
            host=getattr(settings, 'TEST_DB_HOST', None),
            port=getattr(settings, 'TEST_DB_PORT', None),
            user=getattr(settings, 'TEST_DB_USER', None),
            passwd=getattr(settings, 'TEST_DB_PASSWORD', None)
        )
        # exclude elements with None values
        self.no_db_connect_args = dict(
            [
                (k, v) for k, v in no_db_connect_args.iteritems()
                if v is not None])
        utils.drop_schema_if_exists(
            settings.TEST_DB_NAME, connect_args=self.no_db_connect_args)
        utils.create_schema(
            settings.TEST_DB_NAME, connect_args=self.no_db_connect_args)

        self.connect_args = self.no_db_connect_args.copy()
        self.connect_args['db'] = settings.TEST_DB_NAME

        self.user_dev = models.User.objects.get(name='dev')
        self.user_dba = models.User.objects.get(name='dba')
        self.user_admin = models.User.objects.get(name='admin')

        self.server = models.Server.objects.create(
            name='localhost', hostname='localhost')
        self.database_schema = models.DatabaseSchema.objects.create(
            name=settings.TEST_DB_NAME)

        # create initial schema version
        dump = utils.mysql_dump(**self.connect_args)
        self.initial_schema_version = models.SchemaVersion.objects.create(
            database_schema=self.database_schema,
            ddl=dump, checksum=utils.schema_hash(dump))

    def tearDown(self):
        utils.drop_schema_if_exists(
            settings.TEST_DB_NAME, connect_args=self.no_db_connect_args)

    @override_settings(
        AWS_MYSQL_START_WAIT=0, DEV_NO_EC2_APPLY_CHANGESET=True)
    def test_changeset_apply(self):
        """Tests changeset apply."""

        changeset = models.Changeset.objects.create(
            database_schema=self.database_schema,
            type=models.Changeset.DDL_TABLE_CREATE,
            classification=models.Changeset.CLASSIFICATION_PAINLESS,
            submitted_by=self.user_dev,
            submitted_at=timezone.now(),
            review_status=models.Changeset.REVIEW_STATUS_NEEDS
        )

        changeset_detail0 = models.ChangesetDetail.objects.create(
            changeset=changeset,
            type=models.ChangesetDetail.TYPE_ADD,
            description='Add people table.',
            apply_sql="""
                CREATE TABLE people (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    name VARCHAR(255),
                    email VARCHAR(255),
                    dept VARCHAR(255)) ENGINE=InnoDB DEFAULT CHARSET=utf8;
                """,
            revert_sql='DROP TABLE people',
        )

        changeset_detail1 = models.ChangesetDetail.objects.create(
            changeset=changeset,
            type=models.ChangesetDetail.TYPE_INS,
            description='Insert people rows.',
            apply_sql="""
                INSERT INTO people
                VALUES
                    (1, 'moss', 'moss@example.com', 'tools'),
                    (2, 'rod', 'rod@example.com', 'tools'),
                    (3, 'laine', 'laine@example.com', 'leadership'),
                    (4, 'charlie', 'charlie@example.com', 'leadership'),
                    (5, 'jay', 'jay@example.com', 'leadership')
                """,
            revert_sql="""
                DELETE FROM people
                WHERE id in (1, 2, 3, 4, 5)
                """,
            count_sql="""
                SELECT COUNT(*) FROM people
                WHERE dept='tools' AND id IN (1, 2);
                SELECT COUNT(*) FROM people
                WHERE dept='leadership' AND id IN (3, 4, 5);
                SELECT COUNT(*) FROM people
                WHERE id IN (1, 2, 3, 4, 5)
                """
        )

        changeset_review = changeset_review_logic.ChangesetReview(
            changeset, self.initial_schema_version, self.user_dba)
        changeset_review.run()

        changeset = models.Changeset.objects.get(pk=changeset.id)
        self.assertEqual(
            changeset.review_status,
            models.Changeset.REVIEW_STATUS_IN_PROGRESS)

        # delete and recreate schema to prepare for changeset apply
        utils.drop_schema_if_exists(
            settings.TEST_DB_NAME, connect_args=self.no_db_connect_args)
        utils.create_schema(
            settings.TEST_DB_NAME, connect_args=self.no_db_connect_args)

        changeset_apply = changeset_apply_logic.ChangesetApply(
            changeset, self.user_dba, self.server, self.connect_args)
        changeset_apply.run()

        self.assertEqual(models.ChangesetDetailApply.objects.filter(
            changeset_detail__id__in=[
                changeset_detail0.id,
                changeset_detail1.id]).count(),
            2)

        conn = MySQLdb.connect(**self.connect_args)
        statements = """
            SELECT COUNT(*) FROM people
            WHERE dept='tools' AND id IN (1, 2);
            SELECT COUNT(*) FROM people
            WHERE dept='leadership' AND id IN (3, 4, 5);
            SELECT COUNT(*) FROM people
            WHERE id IN (1, 2, 3, 4, 5)
            """
        with conn as cursor:
            self.assertEqual(
                utils.execute_count_statements(cursor, statements),
                [2, 3, 5])
        conn.close()
