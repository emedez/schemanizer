from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from utils import models as utils_models, mysql_functions, helpers
from servers import models as servers_models


class DatabaseSchema(utils_models.TimeStampedModel):
    name = models.CharField(max_length=255, default='')

    class Meta:
        db_table = 'database_schemas'

    def __unicode__(self):
        return self.name

    def get_latest_schema_version(self):
        schema_versions = SchemaVersion.objects.filter(
            database_schema=self).order_by('-updated_at', 'id')
        if schema_versions.exists():
            return schema_versions[0]
        else:
            return None

    def generate_server_data(self, servers, connection_options=None):
        if connection_options is None:
            connection_options = {}
        for server in servers:
            schema_exists = server.schema_exists(
                self.name, connection_options)
            if schema_exists:
                schema_dump = server.dump_schema(self.name, connection_options)
            else:
                schema_dump = ''
            schema_hash = mysql_functions.generate_schema_hash(schema_dump)
            schema_version = None
            try:
                schema_version = SchemaVersion.objects.get(
                    database_schema=self, checksum=schema_hash)
            except ObjectDoesNotExist:
                pass
            schema_version_diff = ''

            if schema_version is None:
                # get different of host schema from latest schema version
                latest_schema_version = self.get_latest_schema_version()
                latest_schema_version_ddl = ''
                if latest_schema_version:
                    latest_schema_version_ddl = latest_schema_version.ddl
                schema_version_diff = helpers.generate_delta(
                    latest_schema_version_ddl,
                    schema_dump,
                    fromfile='saved version', tofile='host version')

            server_data, created = servers_models.ServerData.objects.get_or_create(
                server=server, database_schema=self,
                defaults={
                    'schema_exists': schema_exists,
                    'schema_version': schema_version,
                    'schema_version_diff': schema_version_diff
                })
            if not created:
                server_data.schema_exists = schema_exists
                server_data.schema_version = schema_version
                server_data.schema_version_diff = schema_version_diff
                server_data.save()


class SchemaVersion(utils_models.TimeStampedModel):
    database_schema = models.ForeignKey(DatabaseSchema)
    ddl = models.TextField(blank=True, default='')
    checksum = models.CharField(max_length=255, blank=True, default='')
    pulled_from = models.ForeignKey(
        'servers.Server', null=True, blank=True, default=None,
        db_column='pulled_from', related_name='+')
    pull_datetime = models.DateTimeField(null=True, blank=True, default=None)

    class Meta:
        db_table = 'schema_versions'
        unique_together = (('database_schema', 'checksum'),)

    def __unicode__(self):
        return 'SchemaVersion: id=%s, database_schema=%s' % (
            self.pk, self.database_schema)