import logging

from django.conf import settings
import django.contrib.sites.models as sites_models
import django.contrib.sites
from django.db.models import signals

log = logging.getLogger(__name__)


def create_site(app, created_models, verbosity, **kwargs):
    """Create the default site when we install the sites framework."""

    log.debug('create_site')

    if sites_models.Site in created_models:
        site_id = settings.SITE_ID
        site_name = getattr(settings, 'SITE_NAME', 'Schemanizer')
        site_domain = getattr(settings, 'SITE_DOMAIN', 'example.com')

        qs = sites_models.Site.objects.all().filter(pk=site_id)
        if qs.exists():
            site = qs[0]
            site.name = site_name
            site.domain = site_domain
            site.save()
            log.debug('Updated site object.')
        else:
            site = django.contrib.sites.models.Site()
            site.pk = site_id
            site.name = site_name
            site.domain = site_domain
            site.save()
            log.debug('Created site object.')


signals.post_syncdb.connect(create_site, sender=sites_models)