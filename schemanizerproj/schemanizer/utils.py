"""Utility functions."""
import hashlib
import logging
import re
import shlex
import StringIO
import struct
import subprocess
import time

import mmh3

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


def generate_request_id(request):
    """Create a unique ID for the request."""

    s = hashlib.sha1()
    s.update(str(time.time()))
    s.update(request.META['REMOTE_ADDR'])
    s.update(request.META['SERVER_NAME'])
    s.update(request.get_full_path())
    h = s.hexdigest()
    #l = long(h, 16)

    # shorten ID
    #tag = struct.pack('d', l).encode('base64').replace('\n', '').strip('=')
    return h


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


def mysql_dump(db, host=None, port=None, user=None, passwd=None):
    cmd = u'mysqldump'
    if host:
        cmd += u' -h %s' % (host,)
    if port:
        cmd += u' -P %s' % (port,)
    if user:
        cmd += u' -u %s' % (user,)
    if passwd:
        cmd += u' -p%s' % (passwd,)
    cmd += u' -d --skip-add-drop-table --skip-comments %s' % (db,)
    log.debug(cmd)
    args = shlex.split(str(cmd))

    ret = ''
    p = subprocess.Popen(args, stdout=subprocess.PIPE)
    try:
        while True:
            ln = p.stdout.readline()
            ret += ln
            if ln == '' and p.poll() is not None:
                break
    finally:
        p.wait()

    pattern = r'AUTO_INCREMENT=\d+\s*'
    prog = re.compile(pattern, re.IGNORECASE)
    ret = prog.sub('', ret)
    return ret


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
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data = None
    try:
        stdout_data = p.communicate(input=query_string)[0]
    finally:
        p.wait()
    return stdout_data



def hash_string(s):
    """Creates hash for the string."""

    k1, k2 = mmh3.hash64(s)
    anded = 0xFFFFFFFFFFFFFFFF
    h = '%016x%016x' % (k1 & anded, k2 & anded)
    return h