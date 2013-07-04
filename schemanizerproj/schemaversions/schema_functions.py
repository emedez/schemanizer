from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from schemanizer.logic import privileges_logic
from utils import mysql_functions
from . import models


def generate_schema_version(server, schema_name, connection_options=None):
    if connection_options is None:
        connection_options = {}

    schema_dump = server.dump_schema(schema_name, connection_options)

    #
    # Save dump as latest version for the schema
    #
    database_schema, __ = models.DatabaseSchema.objects.get_or_create(
        name=schema_name)
    checksum = mysql_functions.generate_schema_hash(schema_dump)
    schema_version_created = False
    try:
        schema_version = models.SchemaVersion.objects.get(
            database_schema=database_schema,
            checksum=checksum)
        schema_version.ddl = schema_dump
        schema_version.pulled_from = server
        schema_version.pull_datetime = timezone.now()
        schema_version.save()
    except ObjectDoesNotExist:
        schema_version = models.SchemaVersion.objects.create(
            database_schema=database_schema,
            ddl=schema_dump,
            checksum=mysql_functions.generate_schema_hash(schema_dump),
            pulled_from=server,
            pull_datetime=timezone.now())
        schema_version_created = True

    return (schema_version, schema_version_created)


def save_schema_dump(
        server, database_schema_name, perform_checks=False, check_user=None):
    """Creates database schema (if needed) and schema version."""

    if perform_checks:
        privileges_logic.UserPrivileges(check_user).check_save_schema_dump()

    conn_opts = {}
    conn_opts['host'] = server.hostname
    if server.port:
        conn_opts['port'] = server.port
    if settings.MYSQL_USER:
        conn_opts['user'] = settings.MYSQL_USER
    if settings.MYSQL_PASSWORD:
        conn_opts['passwd'] = settings.MYSQL_PASSWORD

    structure = mysql_functions.dump_schema(database_schema_name, **conn_opts)
    checksum = mysql_functions.generate_schema_hash(structure)

    database_schema, __ = (
        models.DatabaseSchema.objects.get_or_create(
            name=database_schema_name))
    schema_version, __ = (
        models.SchemaVersion.objects.get_or_create(
            database_schema=database_schema,
            checksum=checksum))

    schema_version.ddl=structure
    schema_version.checksum=checksum
    schema_version.pulled_from = server
    schema_version.pull_datetime = timezone.now()
    schema_version.save()

    return schema_version