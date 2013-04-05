import logging
import time

import MySQLdb

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User as AuthUser
from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.core.urlresolvers import reverse

from django.utils import timezone

import boto.ec2


from schemanizer import models
from schemanizer import utils

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


def apply_changesets(request, database_schema):
    """Launches and EC2 instance and applies changesets for the schema."""

    aws_access_key_id=settings.AWS_ACCESS_KEY_ID
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY

    region = settings.AWS_REGION
    ami_id = settings.AWS_AMI_ID
    key_name = settings.AWS_KEY_NAME
    security_groups = settings.AWS_SECURITY_GROUPS
    instance_type = settings.AWS_INSTANCE_TYPE

    conn = boto.ec2.connect_to_region(
        region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key)

    reservation = conn.run_instances(
        ami_id,
        key_name=key_name,
        instance_type=instance_type,
        security_groups=security_groups)
    log.debug('reservation: %s' % (reservation,))

    if reservation:
        instances = reservation.instances
        log.debug('instances: %s' % (instances,))

        if instances:
            instance = instances[0]

            orig_tries = tries = 60
            while (tries > 0) and (instance.state != 'running'):
                time.sleep(1)
                instance.update()
                tries -= 1

            if instance.state == 'running':
                msg = u'EC2 instance started.'
                log.info(msg)
                messages.info(request, msg)

                mysql_conn = create_aws_mysql_connection()
                query = 'CREATE SCHEMA IF NOT EXISTS %s' % (database_schema.name,)
                utils.execute(mysql_conn, query)

                schema_versions = models.SchemaVersion.objects.filter(
                    database_schema=database_schema).order_by('-created_at', '-id')
                schema_version = None
                if schema_versions.count() > 0:
                    schema_version = schema_versions[0]
                if schema_version:
                    mysql_conn.close()
                    mysql_conn = create_aws_mysql_connection(db=database_schema.name)
                    utils.execute(mysql_conn, schema_version.ddl)

                    changesets = models.Changeset.objects.get_not_deleted(
                        ).select_related().filter(
                        review_status=models.Changeset.REVIEW_STATUS_APPROVED)
                    for changeset in changesets:
                        for changeset_detail in changeset.changeset_details.select_related().order_by('id'):
                            try:
                                results = utils.fetchall(mysql_conn, changeset_detail.apply_sql)
                                models.ChangesetDetailApply.objects.create(
                                    changeset_detail=changeset_detail,
                                    before_version=schema_version.id,
                                    results_log=u'%s' % (results,)
                                )
                            except Exception, e:
                                log.exception('EXCEPTION')
                                messages.error(request, e.message)
                    msg = u'Apply changesets completed. Login as admin and go to /admin pages to view changeset detail applies.'
                    log.info(msg)
                    messages.info(request, msg)

                else:
                    msg = u'No schema version found.'
                    log.error(msg)
                    messages.error(request, msg)

                instance.terminate()
                msg = u'EC2 instance terminated.'
                log.info(msg)
                messages.info(request, msg)
            else:
                msg = u"Instance state did not reach 'running' after checking for %s times." % (orig_tries,)
                log.error(msg)
                messages.error(request, msg)
        else:
            msg = u'No EC2 instances were returned.'
            log.warn(msg)
            messages.warning(request, msg)
    else:
        msg = u'No AWS reservation was returned.'
        log.warn(msg)
        messages.warning(request, msg)


def create_aws_mysql_connection(db=None):
    """Creates connection to MySQL on EC2 instance."""
    connection_options = {}
    if settings.AWS_MYSQL_HOST:
        connection_options['host'] = settings.AWS_MYSQL_HOST
    if settings.AWS_MYSQL_PORT:
        connection_options['port'] = settings.AWS_MYSQL_PORT
    if settings.AWS_MYSQL_USER:
        connection_options['user'] = settings.AWS_MYSQL_USER
    if settings.AWS_MYSQL_PASSWORD:
        connection_options['passwd'] = settings.AWS_MYSQL_PASSWORD
    if db:
        connection_options['db'] = db
    return MySQLdb.connect(**connection_options)