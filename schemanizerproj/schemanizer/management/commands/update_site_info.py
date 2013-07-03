import logging

from django.conf import settings
from django.core.management.base import BaseCommand

log = logging.getLogger(__name__)


class Command(BaseCommand):
    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        from django.contrib import sites
        qs = sites.models.Site.objects.all().filter(pk=settings.SITE_ID)
        if qs.exists():
            site = qs[0]
            site.name = settings.SITE_NAME
            site.domain = settings.SITE_DOMAIN
            site.save()
            log.debug('Updated site.')
        else:
            site = sites.models.Site()
            site.pk = settings.SITE_ID
            site.name = settings.SITE_NAME
            site.domain = settings.SITE_DOMAIN
            site.save()
            log.debug('Created site.')