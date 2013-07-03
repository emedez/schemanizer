from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
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

