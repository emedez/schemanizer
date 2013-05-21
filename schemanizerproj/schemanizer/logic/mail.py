"""Email-related logic."""

import logging

from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse

from schemanizer import models

log = logging.getLogger(__name__)


def send_mail(
        subject='', body='', from_email=None, to=None, bcc=None,
        connection=None, attachments=None, headers=None,
        cc=None):
    """Sends email."""

    text_content = body

    if to and not isinstance(to, list) and not isinstance(to, tuple):
        to = [to]
    if bcc and not isinstance(bcc, list) and not isinstance(bcc, tuple):
        bcc = [bcc]
    if cc and not isinstance(cc, list) and not isinstance(cc, tuple):
        cc = [cc]
    msg = EmailMessage(
        subject, text_content, from_email, to, bcc=bcc,
        connection=connection, attachments=attachments, headers=headers,
        cc=cc)
    msg.send()


def send_changeset_reviewed_mail(changeset):
    """Sends reviewed changeset email to dbas."""

    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    to = list(
        models.User.objects.values_list('email', flat=True)
            .filter(role__name=models.Role.ROLE_DBA))

    if to:
        subject = 'Changeset reviewed'
        body = u'The following is the URL for the changeset that was reviewed by %s: \n%s' % (
            changeset.reviewed_by.name, changeset_url)
        send_mail(subject=subject, body=body, to=to)
        log.info(u'Reviewed changeset email sent to: %s' % (to,))
    else:
        log.warn('No email recipients.')
