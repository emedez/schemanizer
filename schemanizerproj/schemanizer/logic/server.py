"""Server logic."""
import logging

from django.conf import settings
from django.db import transaction

from schemanizer import models, utils
from schemanizer.logic import (
    privileges as logic_privileges)

log = logging.getLogger(__name__)


def save_schema_dump(server, database_schema_name, user):
    """Creates database schema (if needed) and schema version."""

    server = utils.get_model_instance(server, models.Server)
    user = utils.get_model_instance(user, models.User)

    logic_privileges.UserPrivileges(user).check_save_schema_dump()

    conn_opts = {}
    conn_opts['host'] = server.hostname
    if server.port:
        conn_opts['port'] = server.port
    if settings.AWS_MYSQL_USER:
        conn_opts['user'] = settings.AWS_MYSQL_USER
    if settings.AWS_MYSQL_PASSWORD:
        conn_opts['passwd'] = settings.AWS_MYSQL_PASSWORD

    structure = utils.mysql_dump(database_schema_name, **conn_opts)

    with transaction.commit_on_success():
        database_schema, __ = models.DatabaseSchema.objects.get_or_create(
            name=database_schema_name)
        schema_version = models.SchemaVersion.objects.create(
            database_schema=database_schema, ddl=structure,
            checksum=utils.schema_hash(structure))

    return schema_version