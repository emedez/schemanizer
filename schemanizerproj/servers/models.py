import MySQLdb
from django.db import models
from utils import models as utils_models, mysql_functions


class Environment(utils_models.TimeStampedModel):
    """Environment"""

    name = models.CharField(max_length=255, default='')

    class Meta:
        db_table = 'environments'

    def __unicode__(self):
        """Returns unicode representation of the object."""
        return self.name


class Server(utils_models.TimeStampedModel):
    """Server"""

    name = models.CharField(
        max_length=255, unique=True, default='')
    hostname = models.CharField(max_length=255, default='')
    environment = models.ForeignKey(
        Environment, null=True, blank=True, default=None,
        on_delete=models.SET_NULL)
    port = models.IntegerField(null=True, blank=True, default=None)

    class Meta:
        db_table = 'servers'

    def __unicode__(self):
        """Returns unicode representation of the object."""
        parts = []
        parts.append(self.name)
        parts.append(' [%s' % self.hostname)
        if self.port is None:
            parts.append(']')
        else:
            parts.append(':%s]' % self.port)
        if self.environment:
            parts.append(', environment=%s' % self.environment)
        return ''.join(parts)

    def schema_exists(self, schema_name, connection_options=None):
        return schema_name in self.get_schema_list(connection_options)

    def get_schema_list(self, connection_options=None):
        if connection_options is None:
            connection_options = {}
        connection_options.update({'host': self.hostname})
        if self.port:
            connection_options['port'] = self.port
        conn = MySQLdb.connect(**connection_options)
        schema_list = []
        with conn as cur:
            cur.execute('SHOW DATABASES')
            rows = cur.fetchall()
            for row in rows:
                if row[0] not in ['information_schema', 'mysql']:
                    schema_list.append(row[0])
        return schema_list

    def dump_schema(self, schema_name, connection_options=None):
        if connection_options is None:
            connection_options = {}
        connection_options.update({'host': self.hostname})
        if self.port:
            connection_options['port'] = self.port
        return mysql_functions.dump_schema(schema_name, **connection_options)


class ServerData(utils_models.TimeStampedModel):
    server = models.ForeignKey(Server)
    database_schema = models.ForeignKey('schemaversions.DatabaseSchema')
    schema_exists = models.BooleanField(default=False)
    schema_version = models.ForeignKey(
        'schemaversions.SchemaVersion', null=True, blank=True, default=None,
        on_delete=models.SET_NULL)
    schema_version_diff = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'server_data'
        unique_together = (('server', 'database_schema'),)