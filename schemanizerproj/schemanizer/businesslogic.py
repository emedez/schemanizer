import logging

from django.contrib.auth.models import User as AuthUser
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse
from django.utils import timezone

from schemanizer import models

log = logging.getLogger(__name__)


def update_user(id, name, email, role):
    """Updates user."""
    user = models.User.objects.get(id=id)
    user.name = name
    user.email = email
    user.role = role
    user.save()

    auth_user = user.auth_user
    auth_user.username = user.name
    auth_user.email = user.email
    auth_user.save()

    log.info('User [id=%s] was updated.' % (id,))

    return user


def create_user(name, email, role, password):
    """Creates user."""
    auth_user = AuthUser.objects.create_user(name, email, password)
    user = models.User.objects.create(name=name, email=email, role=role, auth_user=auth_user)
    log.info('User %s created.' % (name,))
    return user


def send_mail(
        subject='', body='', from_email=None, to=None, bcc=None,
        connection=None, attachments=None, headers=None, alternatives=None,
        cc=None):
    text_content = body
    html_content = body

    if to and not isinstance(to, list) and not isinstance(to, tuple):
        to = [to]
    if bcc and not isinstance(bcc, list) and not isinstance(bcc, tuple):
        bcc = [bcc]
    if cc and not isinstance(cc, list) and not isinstance(cc, tuple):
        cc = [cc]
    msg = EmailMultiAlternatives(
        subject, text_content, from_email, to,
        bcc=bcc,
        connection=connection,
        attachments=attachments,
        headers=headers,
        alternatives=alternatives,
        cc=cc)
    msg.attach_alternative(html_content, 'text/html')
    msg.send()


def send_changeset_submitted_mail(changeset):
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    to = list((
        models.User.objects.values_list('email', flat=True)
        .filter(role__name=models.Role.ROLE_DBA)))

    if to:
        subject = u'New submitted changeset'
        body = (
            u'New changeset was submitted by %s: \n'
            u'%s') % (changeset.submitted_by.name, changeset_url,)
        send_mail(subject=subject, body=body, to=to)
        log.info('New submitted changeset email sent to: %s' % (to,))
    else:
        log.warn('No email recipients.')


def send_changeset_reviewed_mail(changeset):
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    #to = list((
    #    models.User.objects.values_list('email', flat=True)
    #    .filter(role__name=models.Role.ROLE_DBA)))
    to = [changeset.reviewed_by.email]

    if to:
        subject = u'Changeset reviewed'
        body = (
            u'Changeset was reviewed by %s: \n'
            u'%s') % (changeset.reviewed_by.name, changeset_url,)
        send_mail(subject=subject, body=body, to=to)
        log.info('Reviewed changeset email sent to: %s' % (to,))
    else:
        log.warn('No email recipients.')


def send_changeset_approved_mail(changeset):
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    #to = list((
    #    models.User.objects.values_list('email', flat=True)
    #    .filter(role__name=models.Role.ROLE_DBA)))
    to = [changeset.approved_by.email]

    if to:
        subject = u'Changeset approved'
        body = (
            u'Changeset was approved by %s: \n'
            u'%s') % (changeset.approved_by.name, changeset_url,)
        send_mail(subject=subject, body=body, to=to)
        log.info('Approved changeset email sent to: %s' % (to,))
    else:
        log.warn('No email recipients.')


def send_changeset_rejected_mail(changeset):
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    #to = list((
    #    models.User.objects.values_list('email', flat=True)
    #    .filter(role__name=models.Role.ROLE_DBA)))
    to = [changeset.approved_by.email]

    if to:
        subject = u'Changeset rejected'
        body = (
                   u'Changeset was rejected by %s: \n'
                   u'%s') % (changeset.approved_by.name, changeset_url,)
        send_mail(subject=subject, body=body, to=to)
        log.info('Rejected changeset email sent to: %s' % (to,))
    else:
        log.warn('No email recipients.')


def soft_delete_changeset(changeset):
    """Soft deletes changeset."""
    changeset.is_deleted = 1
    changeset.save()

    models.ChangesetAction.objects.create(
        changeset=changeset,
        type=models.ChangesetAction.TYPE_DELETED,
        timestamp=timezone.now()
    )
    log.info('Changeset [id=%s] was soft deleted.' % (changeset.id,))


def changeset_submit(**kwargs):
    """Submits changeset.

    expected keyword arguments:
        changeset_form
        changeset_detail_formset
        user
            - this is used as value for submitted_by
    """
    now = timezone.now()

    changeset_form = kwargs.get('changeset_form')
    changeset_detail_formset = kwargs.get('changeset_detail_formset')
    submitted_by = kwargs.get('user')
    submitted_at = now

    changeset = changeset_form.save(commit=False)
    changeset.submitted_by = submitted_by
    changeset.submitted_at = submitted_at
    changeset.save()
    changeset_form.save_m2m()
    changeset_detail_formset.save()

    models.ChangesetAction.objects.create(
        changeset=changeset,
        type=models.ChangesetAction.TYPE_CREATED,
        timestamp = now)

    log.info('A changeset was submitted:\n%s' % (changeset,))

    send_changeset_submitted_mail(changeset)

    return changeset


def changeset_review(**kwargs):
    """Reviews changeset.

    expected keyword arguments:
        changeset_form
        changeset_detail_formset
        user
            - this is used as value for reviewed_by
    """
    now = timezone.now()

    changeset_form = kwargs.get('changeset_form')
    changeset_detail_formset = kwargs.get('changeset_detail_formset')
    reviewed_by = kwargs.get('user')

    changeset = changeset_form.save(commit=False)
    changeset.set_reviewed_by(reviewed_by)
    changeset_form.save_m2m()
    changeset_detail_formset.save()

    log.info('A changeset was reviewed:\n%s' % (changeset,))

    send_changeset_reviewed_mail(changeset)

    return changeset


def changeset_approve(**kwargs):
    """Approves changeset.

    expected keyword arguments:
        changeset
        user
    """
    changeset = kwargs.get('changeset')
    user = kwargs.get('user')

    changeset.set_approved_by(user)

    log.info('A changeset was approved:\n%s' % (changeset,))

    send_changeset_approved_mail(changeset)

    return changeset


def changeset_reject(**kwargs):
    """Rejects changeset.

    expected keyword arguments:
        changeset
        user
    """
    changeset = kwargs.get('changeset')
    user = kwargs.get('user')

    changeset.set_rejected_by(user)

    log.info('A changeset was rejected:\n%s' % (changeset,))

    send_changeset_rejected_mail(changeset)

    return changeset