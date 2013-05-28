import logging
import random
import string

from django.conf import settings
from django.test import TestCase

import MySQLdb

from schemanizer import exceptions, utils

log = logging.getLogger(__name__)


def random_table(length=16):
    return ''.join(random.choice(string.lowercase) for i in range(length))


class ExecuteCountStatementsTest(TestCase):
    """execute_count_statements() tests."""

    def setUp(self):
        no_db_connect_args = dict(
            host=getattr(settings, 'TEST_DB_HOST', None),
            port=getattr(settings, 'TEST_DB_PORT', None),
            user=getattr(settings, 'TEST_DB_USER', None),
            passwd=getattr(settings, 'TEST_DB_PASSWORD', None)
        )
        # exclude elements with None values
        self.no_db_connect_args = dict(
            [(k, v) for k, v in no_db_connect_args.iteritems() if v is not None])
        utils.drop_schema_if_exists(
            settings.TEST_DB_NAME, connect_args=self.no_db_connect_args)
        utils.create_schema(
            settings.TEST_DB_NAME, connect_args=self.no_db_connect_args)

        self.connect_args = self.no_db_connect_args.copy()
        self.connect_args['db'] = settings.TEST_DB_NAME

        self.table_name = random_table()

        conn = MySQLdb.connect(**self.connect_args)
        try:
            with conn as cursor:
                try:
                    cursor.execute('drop table if exists %s' % (
                        self.table_name,))
                except Warning, e:
                    log.debug('WARNING %s: %s' % (type(e), e))

                cursor.execute(
                    """
                    create table %s(
                        id int primary key auto_increment,
                        name varchar(255),
                        email varchar(255),
                        dept varchar(255))
                    """ % (self.table_name,))
                cursor.execute(
                    """
                    insert into %s
                    values
                        (1, 'moss', 'moss@example.com', 'tools'),
                        (2, 'rod', 'rod@example.com', 'tools'),
                        (3, 'laine', 'laine@example.com', 'leadership'),
                        (4, 'charlie', 'charlie@example.com', 'leadership'),
                        (5, 'jay', 'jay@example.com', 'leadership')
                    """ % (self.table_name,))
        finally:
            conn.close()

    def tearDown(self):
        utils.drop_schema_if_exists(
            settings.TEST_DB_NAME, connect_args=self.no_db_connect_args)

    def test_single_statement(self):
        """Tests execute_count_statements() with single statement."""

        conn = MySQLdb.connect(**self.connect_args)
        try:
            with conn as cursor:
                self.assertEqual(
                    utils.execute_count_statements(
                        cursor,
                        'select count(*) from %s where id in (1,2,3,4,5)' % (
                            self.table_name,)),
                    [5])
        finally:
            conn.close()

    def test_multiple_statements(self):
        """Tests execute_count_statements with multiple statements."""

        conn = MySQLdb.connect(**self.connect_args)
        try:
            with conn as cursor:
                self.assertEqual(
                    utils.execute_count_statements(
                        cursor,
                        """
                        select count(*) from %s where id in (1,2,3,4,5);
                        select count(*) from %s where dept='tools';
                        select count(*) from %s where dept='leadership';
                        """ % (self.table_name, self.table_name,
                        self.table_name)),
                    [5, 2, 3])
        finally:
            conn.close()

    def test_multiple_columns(self):
        """Tests execute_count_statements() with statement that returns multiple columns."""

        conn = MySQLdb.connect(**self.connect_args)
        try:
            with conn as cursor:
                self.assertRaises(
                    exceptions.Error,
                    utils.execute_count_statements,
                    cursor,
                    'select id, name from %s' % (self.table_name,))
        finally:
            conn.close()

    def test_multiple_rows(self):
        """Tests execute_count_statements() with statement that returns multiple rows."""

        conn = MySQLdb.connect(**self.connect_args)
        try:
            with conn as cursor:
                self.assertRaises(
                    exceptions.Error,
                    utils.execute_count_statements,
                    cursor,
                    'select id from %s' % (self.table_name,))
        finally:
            conn.close()

    def test_no_returned_rows(self):
        """Tests execute_count_statements() with statement that returned no rows."""

        conn = MySQLdb.connect(**self.connect_args)
        try:
            with conn as cursor:
                self.assertRaises(
                    exceptions.Error,
                    utils.execute_count_statements,
                    cursor,
                    'select id from %s where id=-1' % (self.table_name,))
        finally:
            conn.close()

    def test_empty_statement(self):
        """Tests execute_count_statements() with empty statement."""

        conn = MySQLdb.connect(**self.connect_args)
        try:
            with conn as cursor:
                self.assertEqual(
                    utils.execute_count_statements(cursor, ''), [])
        finally:
            conn.close()

    def test_empty_statement_in_the_middle(self):
        """Tests execute_count_statements() with empty statement in the middle."""

        conn = MySQLdb.connect(**self.connect_args)
        try:
            with conn as cursor:
                self.assertEqual(
                    utils.execute_count_statements(
                        cursor,
                        """
                        select count(*) from %s where id in (1, 2, 3);
                        ;
                        select count(*) from %s where id in (4, 5)
                        """ % (self.table_name, self.table_name)),
                    [3, None, 2])
        finally:
            conn.close()