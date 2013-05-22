"""Email-related logic."""

import logging

from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse

from schemanizer import models, utils

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
    changeset = utils.get_model_instance(changeset, models.Changeset)

    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    to = list(
        models.User.objects.values_list('email', flat=True)
            .filter(role__name=models.Role.ROLE_DBA))
    submitter_email = changeset.submitted_by.email
    if not submitter_email in to:
        to.append(submitter_email)

    if to:
        subject = 'Changeset reviewed'
        body_lines = []
        body_lines.append(
            u'The following is the URL for the changeset that was reviewed '
            u'by %s:' % (changeset.reviewed_by.name,))
        body_lines.append(changeset_url)
        body_lines.append('')
        if changeset.review_status == models.Changeset.REVIEW_STATUS_IN_PROGRESS:
            body_lines.append(
                u'Changeset was successfully reviewed with no errors.')
        elif changeset.review_status == models.Changeset.REVIEW_STATUS_REJECTED:
            body_lines.append(u'The changeset was rejected.')
        body_lines.append(u'The results can be found on:')
        body_lines.append(
            'http://%s%s'  % (site.domain, reverse(
                'schemanizer_changeset_view_review_results',
                args=[changeset.id])))
        body = u'\n'.join(body_lines)
#        body = (
#            u'The following is the URL for the changeset that was reviewed '
#            u'by %s: \n%s' % (
#                changeset.reviewed_by.name, changeset_url))
        send_mail(subject=subject, body=body, to=to)
        log.debug(u'Reviewed changeset email sent to: %s' % (to,))
    else:
        log.warn('No email recipients.')
