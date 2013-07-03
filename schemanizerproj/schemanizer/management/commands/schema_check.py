import logging
from optparse import make_option
from django.core.management.base import BaseCommand
from schemaversions import models as schemaversions_models
from servers import models as servers_models

log = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        try:
            database_schemas = schemaversions_models.DatabaseSchema.objects.all()
            server_list = list(servers_models.Server.objects.all())
            for database_schema in database_schemas:
                print "Schema: %s" % database_schema.name
                for server in server_list:
                    try:
                        print "    processing host %s..." % server.hostname
                        database_schema.generate_server_data([server])
                    except Exception, e:
                        log.exception('EXCEPTION')
                        print '        ERROR %s: %s' % (type(e), e)
        except Exception, e:
            log.exception('EXCEPTION')
        finally:
            print 'schema_check finished.'
