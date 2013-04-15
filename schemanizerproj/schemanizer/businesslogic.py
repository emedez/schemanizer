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

    log.info(u'User [id=%s] was updated.' % (id,))

    return user


def create_user(name, email, role, password):
    """Creates user."""
    auth_user = AuthUser.objects.create_user(name, email, password)
    user = models.User.objects.create(name=name, email=email, role=role, auth_user=auth_user)
    log.info(u'User [id=%s] was created.' % (user.id,))
    return user


def delete_user(user):
    """Deletes user."""
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)
    auth_user = user.auth_user
    user_id = user.id
    auth_user.delete()
    log.info(u'User [id=%s] was deleted.' % (user_id,))


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
        log.info(u'New submitted changeset email sent to: %s' % (to,))
    else:
        log.warn(u'No email recipients.')


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


def delete_changeset(changeset):
    """Deletes changeset."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)

    changeset_id = changeset.id
    changeset.delete()
    log.info('Changeset [id=%s] was deleted.' % (changeset_id,))


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

    log.info(u'A changeset was submitted:\n%s' % (changeset,))

    send_changeset_submitted_mail(changeset)

    return changeset


def update_changeset(**kwargs):
    """Updates changeset.

    expected keyword arguments:
        changeset_form
        changeset_detail_formset
        user
    """
    changeset_form = kwargs.get('changeset_form')
    changeset_detail_formset = kwargs.get('changeset_detail_formset')
    updated_by = kwargs.get('user')

    changeset = changeset_form.save(commit=False)
    changeset.set_updated_by(updated_by)
    changeset_form.save_m2m()
    changeset_detail_formset.save()

    log.info(u'Changeset was updated:\n%s' % (changeset,))

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


def apply_changeset(schema_version_id, changeset_id):
    """Launches and EC2 instance and applies changesets for the schema."""

    no_ec2 = settings.DEV_NO_EC2_APPLY_CHANGESET
    if no_ec2:
        log.info(u'No EC2 instances will be started.')

    schema_version = models.SchemaVersion.objects.get(pk=schema_version_id)
    database_schema = schema_version.database_schema
    changeset = models.Changeset.objects.get(pk=changeset_id)
    if changeset.database_schema_id != schema_version.database_schema_id:
        raise Exception(u'Schema version and changeset do not have the same database schema.')

    aws_access_key_id=settings.AWS_ACCESS_KEY_ID
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY

    region = settings.AWS_REGION
    ami_id = settings.AWS_AMI_ID
    key_name = settings.AWS_KEY_NAME
    security_groups = settings.AWS_SECURITY_GROUPS
    instance_type = settings.AWS_INSTANCE_TYPE

    if not no_ec2:
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

    if no_ec2 or reservation:
        if not no_ec2:
            instances = reservation.instances
        try:
            if not no_ec2:
                log.debug('instances: %s' % (instances,))

            if no_ec2 or instances:
                if not no_ec2:
                    instance = instances[0]
                    time.sleep(settings.AWS_EC2_INSTANCE_START_WAIT)
                    tries = 0
                    start_time = time.time()
                    while True:
                        try:
                            tries += 1
                            log.debug(u'Waiting for instance to run... (tries=%s)' % (tries,))
                            instance.update()
                            if instance.state == 'running':
                                break
                        except:
                            log.exception(u'EXCEPTION')
                        finally:
                            time.sleep(1)
                            elapsed_time = time.time() - start_time
                            if elapsed_time > settings.AWS_EC2_INSTANCE_STATE_CHECK_TIMEOUT:
                                log.debug(u'Gave up trying to wait for EC2 instance to run.')
                                break

                if no_ec2 or (instance.state == 'running'):
                    if not no_ec2:
                        msg = u'EC2 instance running.'
                        log.info(msg)
                        host = instance.public_dns_name
                        log.debug('instance.public_dns_name=%s' % (host,))
                    else:
                        host = None
                    mysql_conn = create_aws_mysql_connection(host=host, wait=True)
                    if mysql_conn:
                        query = 'CREATE SCHEMA IF NOT EXISTS %s' % (database_schema.name,)
                        utils.execute(mysql_conn, query)

                        mysql_conn.close()
                        mysql_conn = create_aws_mysql_connection(
                            db=database_schema.name, host=host)
                        utils.execute(mysql_conn, schema_version.ddl)

                        for changeset_detail in changeset.changeset_details.select_related().order_by('id'):
                            cur = None
                            try:
                                cur = mysql_conn.cursor()
                                results_log_items = []
                                affected_rows = cur.execute(changeset_detail.apply_sql)
                                results_log_items.append(u'Affected rows: %s' % (affected_rows,))
                                if cur.messages:
                                    for exc, val in cur.messages:
                                        val_str = u'%s' % (val,)
                                        if val_str not in results_log_items:
                                            results_log_items.append(val_str)
                                if results_log_items:
                                    results_log = u'\n'.join(results_log_items)
                                else:
                                    results_log = ''
                                models.ChangesetDetailApply.objects.create(
                                    changeset_detail=changeset_detail,
                                    before_version=schema_version.id,
                                    results_log=results_log)
                            except Exception, e:
                                if cur:
                                    log.error(cur.messages)
                                log.exception('EXCEPTION')
                                raise
                            finally:
                                if cur:
                                    cur.close()

                        msg = u'Changeset was applied.'
                        log.info(msg)

                    else:
                        msg = u'Unable to connect to MySQL server on EC2 instance.'
                        log.info(msg)
                        raise Exception(msg)
                else:
                    msg = u"Instance state did not reach 'running' state after checking for %s times." % (tries,)
                    log.error(msg)
                    raise Exception(msg)

            else:
                msg = u'No EC2 instances were returned.'
                log.warn(msg)
                raise Exception(msg)
        finally:
            if not no_ec2:
                if instances:
                    for instance in instances:
                        instance.terminate()
                        msg = u'EC2 instance terminated.'
                        log.info(msg)
    else:
        msg = u'No AWS reservation was returned.'
        log.error(msg)
        raise Exception(msg)


def create_aws_mysql_connection(db=None, host=None, wait=False):
    """Creates connection to MySQL on EC2 instance."""
    import time
    conn = None
    connection_options = {}
    if settings.AWS_MYSQL_HOST:
        connection_options['host'] = settings.AWS_MYSQL_HOST
    elif host:
        connection_options['host'] = host
    if settings.AWS_MYSQL_PORT:
        connection_options['port'] = settings.AWS_MYSQL_PORT
    if settings.AWS_MYSQL_USER:
        connection_options['user'] = settings.AWS_MYSQL_USER
    if settings.AWS_MYSQL_PASSWORD:
        connection_options['passwd'] = settings.AWS_MYSQL_PASSWORD
    if db:
        connection_options['db'] = db
    if wait:
        time.sleep(settings.AWS_MYSQL_START_WAIT)
    tries = 0
    start_time = time.time()
    while True:
        try:
            tries += 1
            log.debug(u'Connecting to MySQL server on EC2 instance... (tries=%s)' % (tries,))
            conn = MySQLdb.connect(**connection_options)
            log.debug(u'Connected to MySQL server on EC2 instance.')
            break
        except:
            log.exception(u'EXCEPTION')
            time.sleep(1)
            elapsed_time = time.time() - start_time
            if elapsed_time > settings.AWS_MYSQL_CONNECT_TIMEOUT:
                log.debug(u'Gave up trying to connect to MySQL server on EC2 instance.')
                break
    return conn


def get_applied_changesets(schema_version):
    if isinstance(schema_version, int):
        schema_version = models.SchemaVersion.objects.get(pk=schema_version)

    selected_changesets = []

    changesets = models.Changeset.objects.all()
    for changeset in changesets:
        changeset_detail_applies = models.ChangesetDetailApply.objects.get_by_schema_version_changeset(
            schema_version.id, changeset.id)
        if changeset_detail_applies.count():
            selected_changesets.append(changeset)

    return selected_changesets