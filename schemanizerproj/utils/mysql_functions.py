import logging
import re
import shlex
import string
import subprocess
import sqlparse
from . import hash_functions

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