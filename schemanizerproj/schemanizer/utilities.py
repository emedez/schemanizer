"""Utility functions."""

import logging
import shlex
import subprocess

import MySQLdb

log = logging.getLogger(__name__)


def fetchall(conn, query, args=None):
    """Executes query and returns all rows."""
    rows = None
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        rows = cur.fetchall()
    finally:
        while cur.nextset() is not None:
            pass
        cur.close()
    return rows


def fetchone(conn, query, args=None):
    """Executes query and returns a single row."""
    row = None
    cur = conn.cursor()
    try:
        cur.execute(query, args)
        row = cur.fetchone()
    finally:
        while cur.nextset() is not None:
            pass
        cur.close()
    return row


def execute(conn, query, args=None):
    """Executes query only."""
    cur = conn.cursor()
    try:
        cur.execute(query, args)
    finally:
        while cur.nextset() is not None:
            pass
        cur.close()





def dump_structure(conn, schema=None):
    """Dumps database structure."""

    structure = ''
    with conn as cur:
        if schema:
            cur.execute('USE `%s`' % (schema,))
        cur.execute('SHOW TABLES')
        tables = []
        for table in cur.fetchall():
            tables.append(table[0])
        for table in tables:
            if len(structure) > 0:
                structure += '\n'
            structure += 'DROP TABLE IF EXISTS `%s`;' % (table,)
            cur.execute('SHOW CREATE TABLE `%s`' % (table,))
            structure += '\n%s;\n' % (cur.fetchone()[1])
    return structure





def mysql_load(db, query_string, host=None, port=None, user=None, passwd=None):
    cmd = u'mysqldump'
    if host:
        cmd += u' -h %s' % (host,)
    if port:
        cmd += u' -P %s' % (port,)
    if user:
        cmd += u' -u %s' % (user,)
    if passwd:
        cmd += u' -p%s' % (passwd,)
    cmd += u' %s' % (db,)
    log.debug(cmd)
    args = shlex.split(str(cmd))
    p = subprocess.Popen(
        args, stdout=subprocess.PIPE, stdin=subprocess.PIPE,
        stderr=subprocess.PIPE)
    stdout_data = None
    try:
        stdout_data = p.communicate(input=query_string)[0]
    finally:
        p.wait()
    return stdout_data
























def create_schema(schema_name, cursor=None, connect_args=None):
    """Creates schema.

    If cursor is not None, it will be used,
    otherwise, connect_args will be used.
    """

    locally_created_cursor = False
    conn = None
    if not cursor:
        if connect_args is None:
            connect_args = {}
        conn = MySQLdb.connect(**connect_args)
        cursor = conn.cursor()
        locally_created_cursor = True

    try:
        cursor.execute('CREATE SCHEMA %s' % (schema_name,))
    except Warning, e:
        # log and ignore warnings
        log.warning('WARNING %s: %s', type(e), e, exc_info=1)
    finally:
        if locally_created_cursor:
            cursor.close()
        if conn:
            conn.close()


def drop_schema_if_exists(schema_name, cursor=None, connect_args=None):
    """Drops schema.

    If cursor is not None, it will be used,
    otherwise, connect_args will be used.
    """

    locally_created_cursor = False
    conn = None
    if not cursor:
        if connect_args is None:
            connect_args = {}
        conn = MySQLdb.connect(**connect_args)
        cursor = conn.cursor()
        locally_created_cursor = True

    try:
        cursor.execute('DROP SCHEMA IF EXISTS %s' % (schema_name,))
    except Warning, e:
        # log and ignore warnings
        log.warning('WARNING %s: %s', type(e), e, exc_info=1)
    finally:
        if locally_created_cursor:
            cursor.close()
        if conn:
            conn.close()
