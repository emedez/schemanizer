import logging
from optparse import make_option
from django.core.management.base import BaseCommand
from celery import states
from djcelery import models as djcelery_models
from emails import email_functions
from schemaversions import models as schemaversions_models
from servers import models as servers_models

log = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        try:
            task_states = djcelery_models.TaskState.objects.filter(
                name='changesetapplies.tasks.apply_changeset',
                state__in=states.UNREADY_STATES)
            if not task_states.exists():
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

                server_data_list = list(
                    servers_models.ServerData.objects.filter(
                        schema_version=None))
                if server_data_list:
                    email_functions.send_mail_unknown_schema(server_data_list)
            else:
                print 'Schema check cancelled, there are ongoing changeset applies.'

        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            print msg
            log.exception(msg)

        finally:
            print 'schema_check finished.'
