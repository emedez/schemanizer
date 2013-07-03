"""Server logic."""
import logging
from django.conf import settings
from schemanizer.logic import privileges_logic
from schemaversions import models as schemaversions_models
from utils import mysql_functions, helpers

log = logging.getLogger(__name__)


def save_schema_dump(server, database_schema_name, user):
    """Creates database schema (if needed) and schema version."""
    privileges_logic.UserPrivileges(user).check_save_schema_dump()

    conn_opts = {}
    conn_opts['host'] = server.hostname
    if server.port:
        conn_opts['port'] = server.port
    if settings.AWS_MYSQL_USER:
        conn_opts['user'] = settings.AWS_MYSQL_USER
    if settings.AWS_MYSQL_PASSWORD:
        conn_opts['passwd'] = settings.AWS_MYSQL_PASSWORD

    structure = mysql_functions.dump_schema(database_schema_name, **conn_opts)

    database_schema, __ = (
        schemaversions_models.DatabaseSchema.objects.get_or_create(
            name=database_schema_name))
    schema_version = (
        schemaversions_models.SchemaVersion.objects.create(
            database_schema=database_schema, ddl=structure,
            checksum=mysql_functions.generate_schema_hash(structure)))

    return schema_version