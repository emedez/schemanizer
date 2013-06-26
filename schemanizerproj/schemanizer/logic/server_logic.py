"""Server logic."""
import logging

from django.conf import settings
from django.db import transaction

from schemanizer import models, utilities
from schemanizer.logic import privileges_logic
from schemaversions.models import DatabaseSchema, SchemaVersion
from servers.models import Server
from users.models import User
from utils.helpers import get_model_instance
from utils.mysql_functions import generate_schema_hash

log = logging.getLogger(__name__)


def save_schema_dump(server, database_schema_name, user):
    """Creates database schema (if needed) and schema version."""

    server = get_model_instance(server, Server)
    user = get_model_instance(user, User)

    privileges_logic.UserPrivileges(user).check_save_schema_dump()

    conn_opts = {}
    conn_opts['host'] = server.hostname
    if server.port:
        conn_opts['port'] = server.port
    if settings.AWS_MYSQL_USER:
        conn_opts['user'] = settings.AWS_MYSQL_USER
    if settings.AWS_MYSQL_PASSWORD:
        conn_opts['passwd'] = settings.AWS_MYSQL_PASSWORD

    structure = mysql_dump(database_schema_name, **conn_opts)

    with transaction.commit_on_success():
        database_schema, __ = DatabaseSchema.objects.get_or_create(
            name=database_schema_name)
        schema_version = SchemaVersion.objects.create(
            database_schema=database_schema, ddl=structure,
            checksum=generate_schema_hash(structure))

    return schema_version