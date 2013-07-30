import logging
import re
import shlex
import string
import subprocess
import time
import MySQLdb
import paramiko
import sqlparse
from . import hash_functions, exceptions

log = logging.getLogger(__name__)


def dump_schema(db, host=None, port=None, user=None, passwd=None):
    cmd_parts = ['mysqldump']
    if host:
        cmd_parts.append(' -h %s' % host)
    if port:
        cmd_parts.append(' -P %s' % port)
    if user:
        cmd_parts.append(' -u %s' % user)
    if passwd:
        cmd_parts.append(' -p%s' % passwd)
    cmd_parts.append(' -d --skip-add-drop-table --skip-comments %s' % db)
    cmd = ''.join(cmd_parts)
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


def normalize_schema_dump(dump):
    """Normalizes schema dump."""

    statement_list = sqlparse.split(dump)
    new_statement_list = []
    for statement in statement_list:
        stripped_chars = unicode(string.whitespace + ';')
        statement = statement.strip(stripped_chars)
        if statement:
            if not statement.startswith(u'/*!'):
                # skip processing conditional comments
                new_statement_list.append(statement)
    return u';\n'.join(new_statement_list)


def generate_schema_hash(dump):
    """Returns the hash string of a normalized dump."""
    return hash_functions.generate_hash(normalize_schema_dump(dump))


def execute_count_statements(cursor, statements):
    """Executes count statement(s)."""

    counts = []
    if not statements:
        return counts

    statements = statements.strip(u'%s%s' % (string.whitespace, ';'))
    statement_list = None
    if statements:
        statement_list = sqlparse.split(statements)

    if not statements:
        return counts

    try:
        for statement in statement_list:
            count = None
            statement = statement.rstrip(u'%s%s' % (string.whitespace, ';'))

            if not statement:
                counts.append(count)
                continue

            row_count = cursor.execute(statement)

            if len(cursor.description) > 1:
                raise exceptions.Error(
                    'Statement should return a single value only.')

            if row_count > 1:
                raise exceptions.Error(
                    u'Statement should return a single row only. '
                    u'Statement was: %s' % (statement,)
                )

            if not row_count:
                raise exceptions.Error(
                    u'Statement returned an empty set. '
                    u'Statement was: %s' % (statement,)
                )

            row = cursor.fetchone()
            if row is None:
                raise exceptions.Error(
                    u'Statement returned an empty set. '
                    u'Statement was: %s' % (statement,)
                )

            counts.append(row[0])

    finally:
        while cursor.nextset() is not None:
            pass

    return counts


def execute_statements(cursor, statements):
    """Executes statements."""

    statements = statements.strip(u'%s%s' % (string.whitespace, ';'))
    statement_list = None
    if statements:
        statement_list = sqlparse.split(statements)

    if not statements:
        return

    try:
        for statement in statement_list:
            statement = statement.rstrip(u'%s%s' % (string.whitespace, ';'))

            if not statement:
                continue

            cursor.execute(statement)

            while cursor.nextset() is not None:
                pass

    finally:
        while cursor.nextset() is not None:
            pass


class MySQLServerConnectionTester(object):
    """Contains logic for connecting to a MySQL server to test if it is ready."""

    def __init__(
            self, connection_options=None, connect_pre_delay=None,
            connect_timeout=None, message_callback=None):
        """Initializes object."""

        super(MySQLServerConnectionTester, self).__init__()

        self._connect_pre_delay = connect_pre_delay
        self._connect_timeout = connect_timeout
        self._message_callback = message_callback

        if connection_options is None:
            self._connection_options = {}
        else:
            self._connection_options = connection_options

        self._init_run_vars()

    def _init_run_vars(self):
        """Initializes variables needed when logic is run."""
        self._messages = []

    @property
    def message(self):
        """Returns messages."""
        return self._messages

    def _store_message(self, message, message_type='info'):
        """Stores message."""
        self._messages.append(dict(
            message=message,
            message_type=message_type))
        if self._message_callback:
            self._message_callback(message, message_type)

    def run(self):
        """Creates connection to a MySQL server."""

        self._init_run_vars()

        if self._connect_pre_delay:
            # For hosts that were dynamically started such as EC2 instances,
            # this is to give time for MySQL server to start,
            # before attempting to connect to it.
            self._store_message(
                'Waiting for %s second(s) to give time for MySQL server to start. (connect_pre_delay)' % (
                    self._connect_pre_delay,))
            time.sleep(self._connect_pre_delay)

        # Attempt to connect to MySQL server until connected successfully
        # or timed out.
        conn = None
        tries = 0
        start_time = time.time()
        while True:
            try:
                tries += 1
                msg = 'Connecting to MySQL server, tries=%s.' % (tries,)
                log.info(msg)
                self._store_message(msg)
                conn = MySQLdb.connect(**self._connection_options)
                msg = 'Connected to MySQL server.'
                log.info(msg)
                self._store_message(msg)
                break
            except Exception, e:
                log.exception('EXCEPTION')
                self._store_message(
                    'ERROR %s: %s' % (type(e), e), 'error')

            if (self._connect_timeout and
                    time.time() - start_time > self._connect_timeout):
                msg = 'Gave up trying to connect to MySQL server.'
                log.info(msg)
                self._store_message(msg)
                break
            time.sleep(0.1)
        return conn


def is_mysql_server_running(hostname, username, key_filename=None):
    """Checks if mysql server is running on specified hostname.

    This is done by connecting to the remote host's SSH server using the
    given username, and execute 'service mysql status', so the provided
    user should have the privilege to execute the command.
    """

    params = {
        'hostname': hostname,
        'username': username
    }
    if key_filename:
        params['pkey'] = paramiko.RSAKey.from_private_key_file(key_filename)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(**params)

    try:
        # stdin, stdout, stderr = c.exec_command('service mysql status')
        stdin, stdout, stderr = c.exec_command('mysqladmin ping')
        stdout_string = stdout.read()
        stderr_string = stderr.read()
        log.debug('stdout_string = %s', stdout_string)
        log.debug('stderr_string = %s', stderr_string)
        # mysql_running = any([
        #     # CentOS/Percona
        #     stdout_string.lower().startswith('mysql running'),
        #     # Ubuntu
        #     stdout_string.lower().startswith('mysql start/running')
        # ])
        mysql_running = stdout_string.strip().lower().startswith(
            'mysqld is alive')
    finally:
        c.close()

    return mysql_running


def create_mysql_user(
        mysql_user, mysql_password, hostname, username, key_filename=None):
    """Creates MySQL user on the specified host.

    This is done by connecting to remote host's SSH server and execute
    a MySQL statement.
    """

    params = {
        'hostname': hostname,
        'username': username
    }
    if key_filename:
        params['pkey'] = paramiko.RSAKey.from_private_key_file(key_filename)
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(**params)

    try:
        sql = "CREATE USER '%s'@'%%' IDENTIFIED BY '%s'" % (
            mysql_user, mysql_password)
        cmd = 'mysql -Bse "%s"' % sql
        log.debug('cmd = %s', cmd)
        stdin, stdout, stderr = c.exec_command(cmd)
        stdout_string = stdout.read()
        stderr_string = stderr.read()
        log.debug('stdout_string = %s', stdout_string)
        log.debug('stderr_string = %s', stderr_string)
        if stderr_string:
            raise exceptions.Error(stderr_string)

        sql = "GRANT ALL ON *.* TO '%s'@'%%'" % mysql_user
        cmd = 'mysql -Bse "%s"' % sql
        log.debug('cmd = %s', cmd)
        stdin, stdout, stderr = c.exec_command(cmd)
        stdout_string = stdout.read()
        stderr_string = stderr.read()
        log.debug('stdout_string = %s', stdout_string)
        log.debug('stderr_string = %s', stderr_string)
        if stderr_string:
            raise exceptions.Error(stderr_string)
    finally:
        c.close()
