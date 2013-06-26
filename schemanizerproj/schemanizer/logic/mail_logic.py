"""Email-related logic."""

import logging

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse

from schemanizer import models, utilities
from users.models import Role, User
from utils.helpers import get_model_instance

log = logging.getLogger(__name__)


def send_mail(
        subject='', body='', from_email=None, to=None, bcc=None,
        connection=None, attachments=None, headers=None,
        cc=None):
    """Sends email."""

    if settings.DISABLE_SEND_MAIL:
        return

    if to and not isinstance(to, list) and not isinstance(to, tuple):
        to = [to]
    if bcc and not isinstance(bcc, list) and not isinstance(bcc, tuple):
        bcc = [bcc]
    if cc and not isinstance(cc, list) and not isinstance(cc, tuple):
        cc = [cc]
    msg = EmailMessage(
        subject, body, from_email, to, bcc=bcc,
        connection=connection, attachments=attachments, headers=headers,
        cc=cc)
    msg.send()


def send_changeset_submission_through_repo_failed_mail(
        changeset_content, error_message, file_data, commit_data):
    """Sends changeset-submission-through-repo-failed email."""

    # recipients
    to = list(
        User.objects.values_list('email', flat=True)
        .filter(role__name=Role.ROLE_DBA))

    committer_user = None
    if 'committer' in commit_data and 'login' in commit_data['committer']:
        user_qs = User.objects.filter(
            github_login=commit_data['committer']['login'])
        if user_qs.exists():
            committer_user = user_qs[0]
    if committer_user and committer_user.email not in to:
        to.append(committer_user.email)

    if to:
        subject = u'Changeset submission through repository failed.'
        lines = []

        lines.append(u'Changeset data from repo')
        lines.append(u'========================')
        lines.append(u'')
        lines.append(u'Filename: %s' % (file_data['filename'],))
        lines.append(u'')
        lines.append(u'Content')
        lines.append(u'-------')
        lines.append(u'%s' % (changeset_content,))
        lines.append(u'')
        lines.append(
            u'Changeset submission process failed with the following '
            u'message:')
        lines.append(
            u'-------------------------------------------------------'
            u'--------')

        lines.append(u'%s' % (error_message,))

        send_mail(subject=subject, body=u'\n'.join(lines), to=to)

        log.info(
            u"New changeset-sumission-through-repository-failed email sent "
            u"to: %s" % (to,))

    else:
        log.warn(
            'Changeset-submission-through-repo-failed email has no '
            'recipients.')


def send_changeset_submitted_mail(changeset):
    """Sends changeset submitted email."""

    changeset = get_model_instance(changeset, models.Changeset)

    # urls
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse(
            'schemanizer_changeset_view', args=[changeset.id]))

    # recipients
    to = list(
        User.objects.values_list('email', flat=True)
        .filter(role__name=Role.ROLE_DBA))
    if changeset.submitted_by.email not in to:
        to.append(changeset.submitted_by.email)

    if to:
        subject = u'New submitted changeset'
        body_lines = []
        body_lines.append(u'New changeset was submitted by %s:' % (
            changeset.submitted_by.name,))
        body_lines.append(changeset_url)
        body = u'\n'.join(body_lines)
        send_mail(subject=subject, body=body, to=to)
        log.info(u'New submitted changeset email sent to: %s' % (to,))
    else:
        log.warn('Changeset submitted email has no recipients.')


def send_mail_changeset_reviewed(changeset):
    """Sends reviewed changeset email."""

    changeset = get_model_instance(changeset, models.Changeset)
    changeset_review = models.ChangesetReview.objects.get(changeset=changeset)

    # urls
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    review_results_url = 'http://%s%s'  % (
        site.domain,
        reverse(
            'schemanizer_changeset_view_review_results', args=[changeset.id]))

    # recipients
    to = list(
        User.objects.values_list('email', flat=True)
            .filter(role__name=Role.ROLE_DBA))
    if changeset.submitted_by.email not in to:
        to.append(changeset.submitted_by.email)

    if to:
        subject = 'Changeset reviewed'
        lines = []

        if changeset_review.success:
            lines.append(
                u"The following changeset has been reviewed without errors "
                u"and is ready for approval:")
        else:
            lines.append(
                u"The following changeset has errors and was rejected:")
        lines.append(changeset_url)
        lines.append(u'')
        lines.append(
            u'The results of changeset review process can be viewed at:')
        lines.append(review_results_url)

        if changeset_review.results_log:
            lines.append(u'')
            lines.append(u'Results log:')
            lines.append(u'%s' % (changeset_review.results_log,))

        send_mail(subject=subject, body=u'\n'.join(lines), to=to)

        log.debug(u'Reviewed changeset email sent to: %s' % (to,))
    else:
        log.warn('Changeset review email has no recipients.')


def send_changeset_updated_mail(changeset):
    """Sends changeset updated email."""

    changeset = get_model_instance(changeset, models.Changeset)

    # urls
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))

    # recipients
    to = list(
        User.objects.values_list('email', flat=True)
        .filter(role__name=Role.ROLE_DBA))
    if changeset.submitted_by.email not in to:
        to.append(changeset.submitted_by.email)

    if to:
        subject = u'Changeset updated'
        body_lines = [
            u'The following is the URL for the changeset that was updated:',
            changeset_url
        ]
        body = u'\n'.join(body_lines)
        send_mail(subject=subject, body=body, to=to)
        log.info(u'Changeset updated email sent to: %s' % (to,))
    else:
        log.warn('Changeset updated mail has no recipients.')


def send_changeset_approved_mail(changeset):
    """Sends changeset approved email."""

    changeset = get_model_instance(changeset, models.Changeset)

    # urls
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))

    # recipients
    to = list(
        User.objects.values_list('email', flat=True)
        .filter(role__name=Role.ROLE_DBA))
    if changeset.submitted_by.email not in to:
        to.append(changeset.submitted_by.email)

    if to:
        subject = u'Changeset approved'
        body = (
            u'The following is the URL of the changeset that was approved '
            u'by %s: \n%s' % (
                changeset.approved_by.name, changeset_url,))
        send_mail(subject=subject, body=body, to=to)
        log.info(u'Changeset approved email sent to: %s' % (to,))
    else:
        log.warn('Changeset approved email has no recipients.')


def send_changeset_rejected_mail(changeset):
    """Sends changeset rejected mail."""

    changeset = get_model_instance(changeset, models.Changeset)

    # urls
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    to = list(
        User.objects.values_list('email', flat=True)
        .filter(role__name=Role.ROLE_DBA))
    if changeset.submitted_by.email not in to:
        to.append(changeset.submitted_by.email)

    if to:
        subject = u'Changeset rejected'
        body = (
            u'The following is the URL of the changeset that was rejected '
            u'by %s: \n%s' % (
                changeset.approved_by.name, changeset_url,))
        send_mail(subject=subject, body=body, to=to)
        log.info(u'Changeset rejected email sent to: %s' % (to,))
    else:
        log.warn('Changeset rejected email has no recipients.')


def send_changeset_applied_mail(changeset, changeset_apply):
    """Sends changeset applied email."""

    changeset = get_model_instance(changeset, models.Changeset)
    changeset_apply = get_model_instance(
        changeset_apply, models.ChangesetApply)

    # urls
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))

    # recipients
    to = list(
        User.objects.values_list('email', flat=True)
            .filter(role__name=Role.ROLE_DBA))
    if changeset.submitted_by.email not in to:
        to.append(changeset.submitted_by.email)

    if to:
        subject = 'Changeset applied'
        body_lines = []
        body_lines.append(
            u"The following changeset has been applied at server '%s' "
            u"by %s:" % (
                changeset_apply.server.name, changeset_apply.applied_by))
        body_lines.append(changeset_url)
        body = u'\n'.join(body_lines)
        send_mail(subject=subject, body=body, to=to)
        log.debug(u'Applied changeset email sent to: %s' % (to,))
    else:
        log.warn('Changeset applied email has no recipients.')