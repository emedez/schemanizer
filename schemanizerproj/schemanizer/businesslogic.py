import logging
import string
import threading
import time
import urllib
import warnings

import MySQLdb
warnings.filterwarnings('ignore', category=MySQLdb.Warning)

from django.conf import settings
from django.contrib.auth.models import User as AuthUser
from django.contrib.sites.models import Site
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import transaction

from django.utils import timezone

import boto.ec2
import sqlparse

from schemanizer import exceptions, models, utils

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
        connection=None, attachments=None, headers=None,
        cc=None):
    text_content = body

    if to and not isinstance(to, list) and not isinstance(to, tuple):
        to = [to]
    if bcc and not isinstance(bcc, list) and not isinstance(bcc, tuple):
        bcc = [bcc]
    if cc and not isinstance(cc, list) and not isinstance(cc, tuple):
        cc = [cc]
    msg = EmailMessage(
        subject, text_content, from_email, to,
        bcc=bcc,
        connection=connection,
        attachments=attachments,
        headers=headers,
        cc=cc)
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


def changeset_can_be_soft_deleted_by_user(changeset, user):
    """Checks if the changeset can be soft deleted by user."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if not changeset.pk:
        # Cannot soft delete unsaved changeset.
        return False

    if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
        # dbas and admins can soft delete changeset
        return True

    if user.role.name in (models.Role.ROLE_DEVELOPER,):
        if changeset.review_status != models.Changeset.REVIEW_STATUS_APPROVED:
            # developers can only soft delete changesets that were not yet approved
            return True

    return False


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


def changeset_can_be_updated_by_user(changeset, user):
    """Checks if this changeset can be updated by user."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if not changeset.pk:
        # Cannot update unsaved changesets.
        return False

    if user.role.name in [models.Role.ROLE_DBA, models.Role.ROLE_ADMIN]:
        # dbas and admins can always update changeset.
        return True

    if user.role.name in [models.Role.ROLE_DEVELOPER]:
        # developers can update changesets only if it was not yet approved.
        if changeset.review_status != models.Changeset.REVIEW_STATUS_APPROVED:
            return True

    return False


def changeset_send_updated_mail(changeset):
    """Sends updated changeset email to dbas."""
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    to = list(
        models.User.objects.values_list('email', flat=True)
            .filter(role__name=models.Role.ROLE_DBA)
    )

    if to:
        subject = u'Changeset updated'
        body = u'The following is the URL for the changeset that was updated: \n%s' % (
            changeset_url)
        send_mail(subject=subject, body=body, to=to)
        log.info(u'Updated changeset email sent to: %s' % (to,))
    else:
        log.warn(u'No email recipients.')


def changeset_update(**kwargs):
    """Updates changeset.

    expected keyword arguments:
        changeset_form
        changeset_detail_formset
        user
    """
    changeset_form = kwargs.get('changeset_form')
    changeset_detail_formset = kwargs.get('changeset_detail_formset')
    user = kwargs.get('user')

    changeset = changeset_form.save(commit=False)
    if changeset_can_be_updated_by_user(changeset, user):
        with transaction.commit_on_success():
            #
            # Update changeset
            #
            now = timezone.now()
            changeset.review_status = changeset.REVIEW_STATUS_NEEDS
            changeset.save()
            changeset_form.save_m2m()
            #
            # Save changeset details
            changeset_detail_formset.save()
            #
            # Create entry on changeset actions
            models.ChangesetAction.objects.create(
                changeset=changeset,
                type=models.ChangesetAction.TYPE_CHANGED,
                timestamp=now)

        log.info(u'Changeset [id=%s] was updated.' % (changeset.id,))

        changeset_send_updated_mail(changeset)

    else:
        raise exceptions.NotAllowed(u'User is not allowed to update changeset.')

    return changeset


def changeset_can_be_reviewed_by_user(changeset, user):
    """Checks if changeset review_status can be set to 'in_progress' by user."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if not changeset.pk:
        # reviews are only allowed on saved changesets
        return False

    # Only DBAs and admins can review changeset
    if user.role.name not in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
        return False

    # allow reviews anytime
    return True


def changeset_send_reviewed_mail(changeset):
    """Sends reviewed changeset email to dbas."""
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    to = list(models.User.objects.values_list('email', flat=True)
        .filter(role__name=models.Role.ROLE_DBA))

    if to:
        subject = u'Changeset reviewed'
        body = u'The following is the URL for the changeset that was reviewed by %s: \n%s' % (
            changeset.reviewed_by.name, changeset_url)
        send_mail(subject=subject, body=body, to=to)
        log.info(u'Reviewed changeset email sent to: %s' % (to,))
    else:
        log.warn(u'No email recipients.')


def changeset_validate_no_update_with_where_clause(changeset, user, server=None):
    """Changeset validate no update with where clause."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if not changeset_can_be_reviewed_by_user(changeset, user):
        raise exceptions.NotAllowed(
            u"User '%s' is not allowed to review changeset [id=%s]." % (
                user.name, changeset.id))

    changeset_has_errors = False
    results = dict(
        changeset_validation=None,
        changeset_tests=[],
        changeset_has_errors=changeset_has_errors)

    created_changeset_test_ids = []
    validation_results = []
    where_clause_found = False
    with transaction.commit_on_success():
        for changeset_detail in changeset.changeset_details.all():
            log.debug(u'Validating changeset detail...\nid: %s\napply_sql:\n%s' % (
                changeset_detail.id, changeset_detail.apply_sql))
            started_at = timezone.now()
            try:
                parsed = sqlparse.parse(changeset_detail.apply_sql)
                where_clause_found_on_apply_sql = False
                for stmt in parsed:
                    if stmt.get_type() in [u'INSERT', u'UPDATE', u'DELETE']:
                        for token in stmt.tokens:
                            if type(token) in [sqlparse.sql.Where]:
                                where_clause_found_on_apply_sql = True
                                break
                    if where_clause_found_on_apply_sql:
                        break
                if where_clause_found_on_apply_sql:
                    validation_results.append(u'WHERE clause found on apply_sql (changeset detail ID: %s).' % (changeset_detail.id,))
                    where_clause_found = True

                parsed = sqlparse.parse(changeset_detail.revert_sql)
                where_clause_found_on_revert_sql = False
                for stmt in parsed:
                    if stmt.get_type() in [u'INSERT', u'UPDATE', u'DELETE']:
                        for token in stmt.tokens:
                            if type(token) in [sqlparse.sql.Where]:
                                where_clause_found_on_revert_sql = True
                                break
                    if where_clause_found_on_revert_sql:
                        break
                if where_clause_found_on_revert_sql:
                    validation_results.append(u'WHERE clause found on revert_sql. (changeset detail ID: %s).' % (changeset_detail.id,))
                    where_clause_found = True
            except Exception, e:
                log.exception('EXCEPTION')
                validation_results.append(u'ERROR: %s' % (e,))
                changeset_has_errors = True

            ended_at = timezone.now()

        validation_results_text = u''
        if validation_results:
            validation_results_text = u'\n'.join(validation_results)
        validation_type = models.ValidationType.objects.get(
            name=u'no update with where clause')
        changeset_validation = models.ChangesetValidation.objects.create(
            changeset=changeset,
            validation_type=validation_type,
            timestamp=timezone.now(),
            result=validation_results_text)
        results['changeset_validation'] = changeset_validation

    log.info(u'Changeset no update with where clause validation was completed.')

    results['changeset_has_errors'] = changeset_has_errors or where_clause_found
    return results


def changeset_can_be_approved_by_user(changeset, user):
    """Checks if this changeset can be approved by user."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if not changeset.pk:
        # Cannot approve unsaved changeset.
        return False

    if changeset.review_status == models.Changeset.REVIEW_STATUS_APPROVED:
        # cannot approve, it is already approved
        return False

    if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
        if changeset.review_status in (models.Changeset.REVIEW_STATUS_IN_PROGRESS):
            return True
    else:
        return False


def changeset_can_be_rejected_by_user(changeset, user):
    """Checks if this changeset can be rejected by user."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if not changeset.pk:
        # Cannot reject unsaved changeset.
        return False

    if changeset.review_status == models.Changeset.REVIEW_STATUS_REJECTED:
        # cannot reject, it is already rejected
        return False

    if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
        # allow reject regardless of review status
        return True
    else:
        return False


def changeset_send_approved_mail(changeset):
    """Send email to dbas."""

    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    to = list(models.User.objects.values_list('email', flat=True)
        .filter(role__name=models.Role.ROLE_DBA))

    if to:
        subject = u'Changeset approved'
        body = u'The following is the URL of the changeset that was approved by %s: \n%s' % (
            changeset.approved_by.name, changeset_url,)
        send_mail(subject=subject, body=body, to=to)
        log.info(u'Approved changeset email sent to: %s' % (to,))
    else:
        log.warn(u'No email recipients.')


def changeset_approve(changeset, user):
    """Approves changeset."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if changeset_can_be_approved_by_user(changeset, user):
        now = timezone.now()
        with transaction.commit_on_success():
            #
            # Update changeset
            #
            changeset.review_status = models.Changeset.REVIEW_STATUS_APPROVED
            changeset.approved_by = user
            changeset.approved_at = now
            changeset.save()
            #
            # Create changeset action entry.
            models.ChangesetAction.objects.create(
                changeset=changeset,
                type=models.ChangesetAction.TYPE_CHANGED,
                timestamp=now)

        log.info(u'Changeset [id=%s] was approved.' % (changeset.id,))

        changeset_send_approved_mail(changeset)

    else:
        raise exceptions.NotAllowed(u'User is not allowed to approve changeset.')


def changeset_send_rejected_mail(changeset):
    site = Site.objects.get_current()
    changeset_url = 'http://%s%s' % (
        site.domain,
        reverse('schemanizer_changeset_view', args=[changeset.id]))
    to = list(models.User.objects.values_list('email', flat=True)
        .filter(role__name=models.Role.ROLE_DBA))

    if to:
        subject = u'Changeset rejected'
        body = u'The following is the URL of the changeset that was rejected by %s: \n%s' % (
            changeset.approved_by.name, changeset_url,)
        send_mail(subject=subject, body=body, to=to)
        log.info(u'Rejected changeset email sent to: %s' % (to,))
    else:
        log.warn(u'No email recipients.')


def changeset_reject(changeset, user):
    """Rejects changeset."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if changeset_can_be_rejected_by_user(changeset, user):
        now = timezone.now()
        with transaction.commit_on_success():
            #
            # Update changeset.
            #
            changeset.review_status = models.Changeset.REVIEW_STATUS_REJECTED
            changeset.approved_by = user
            changeset.approved_at = now
            changeset.save()
            #
            # Create changeset actions entry.
            models.ChangesetAction.objects.create(
                changeset=changeset,
                type=models.ChangesetAction.TYPE_CHANGED,
                timestamp=now)

        log.info(u'Changeset [id=%s] was rejected.' % (changeset.id,))

        changeset_send_rejected_mail(changeset)

    else:
        log.debug(u'changeset:\n%s\n\nuser=%s' % (changeset, user.name))
        raise exceptions.NotAllowed(u'User is not allowed to reject changeset.')


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
                        log.debug(u'Database schema \'%s\' was created (if not existed).' % (
                            database_schema.name,))

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


def user_can_validate_changeset(user, changeset):
    """Returns True, if user can validate changeset, otherwise False."""

    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)
    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)

    if (changeset.review_status == models.Changeset.REVIEW_STATUS_APPROVED and
            user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN)):
        return True
    else:
        return False


def changeset_review(changeset, schema_version, request_id, user, server=None):
    """Reviews changeset."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(schema_version) in (int, long):
        schema_version = models.SchemaVersion.objects.get(pk=schema_version)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if changeset_can_be_reviewed_by_user(changeset, user):
        thread = ReviewThread(changeset, schema_version, request_id, user, server)
        thread.start()
        return thread
    else:
        raise exceptions.NotAllowed(u'User is not allowed to set review status to \'in_progress\'.')


class ReviewThread(threading.Thread):
    def __init__(self, changeset, schema_version, request_id, user, server=None):
        super(ReviewThread, self).__init__()
        self.daemon = True

        self.changeset = changeset
        self.schema_version = schema_version
        self.request_id = request_id
        self.user = user
        self.server = server

        self.messages = []
        self.errors = []
        self.changeset_validations = []
        self.changeset_tests = []
        self.review_results_url = None

    def create_aws_mysql_connection(self, db=None, host=None, wait=False):
        """Creates connection to MySQL on EC2 instance."""
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
            #
            # Sleep, to give time for MySQL server on EC2 instance to start,
            # before attempting to connect to it.
            #
            msg = u'Sleeping for %s second(s) to give time for MySQL server on EC2 instance to start.' % (
                settings.AWS_EC2_INSTANCE_START_WAIT,)
            log.info(u'[%s] %s' % (self.request_id, msg))
            self.messages.append((u'info', msg))
            time.sleep(settings.AWS_MYSQL_START_WAIT)

        #
        # Attempt to connect to MySQL server on EC2 instance,
        # until connected successfully or timed out.
        #
        tries = 0
        start_time = time.time()
        while True:
            try:
                tries += 1
                msg = u'Connecting to MySQL server on EC2 instance... (tries=%s)' % (tries,)
                log.info(u'[%s] %s' % (self.request_id, msg))
                self.messages.append((u'info', msg))
                conn = MySQLdb.connect(**connection_options)
                msg = u'Connected to MySQL server on EC2 instance.'
                log.info(u'[%s] %s' % (self.request_id, msg))
                self.messages.append((u'success', msg))
                break
            except Exception, e:
                log.exception(u'[%s] EXCEPTION' % (self.request_id, ))
                msg = u'%s' % (e,)
                self.messages.append((u'error', msg))
                time.sleep(1)
                elapsed_time = time.time() - start_time
                if elapsed_time > settings.AWS_MYSQL_CONNECT_TIMEOUT:
                    log.debug(u'[%s] Gave up trying to connect to MySQL server on EC2 instance.' % (self.request_id,))
                    break
        return conn

    def run(self):
        try:
            msg = u'Review thread started.'
            self.messages.append((u'info', msg))
            log.info(u'[%s] %s' % (self.request_id, msg))

            with transaction.commit_on_success():
                msg = u'Starting syntax validation...'
                self.messages.append((u'info', msg))
                log.info(u'[%s] %s' % (self.request_id, msg))

                no_ec2 = settings.DEV_NO_EC2_APPLY_CHANGESET
                if no_ec2:
                    log.info(u'[%s] No EC2 instances will be started.' % (self.request_id,))

                server = self.server
                schema_version = self.schema_version
                database_schema = schema_version.database_schema
                changeset = self.changeset
                if changeset.database_schema_id != schema_version.database_schema_id:
                    msg = u'Schema version and changeset do not have the same database schema.'
                    log.error(msg)
                    self.errors.append(msg)
                    self.messages.append((u'error', msg))

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
                    log.debug(u'[%s] reservation: %s' % (self.request_id, reservation))

                if no_ec2 or reservation:
                    if not no_ec2:
                        instances = reservation.instances
                    try:
                        if not no_ec2:
                            log.debug(u'[%s] instances: %s' % (self.request_id, instances))

                        if no_ec2 or instances:
                            if not no_ec2:
                                instance = instances[0]

                                #
                                # Sleep, to give time for EC2 instance to reach running state,
                                # before attempting to access it.
                                #
                                msg = u'Sleeping for %s second(s) to give time for EC2 instance to run.' % (
                                    settings.AWS_EC2_INSTANCE_START_WAIT)
                                log.info(u'[%s] %s' % (self.request_id, msg))
                                self.messages.append((u'info', msg))
                                time.sleep(settings.AWS_EC2_INSTANCE_START_WAIT)

                                #
                                # Poll EC2 instance state until instance state becomes running,
                                # or timed out.
                                #
                                tries = 0
                                start_time = time.time()
                                while True:
                                    try:
                                        tries += 1
                                        msg = u'Waiting for instance to run... (tries=%s)' % (tries,)
                                        log.info(u'[%s] %s' % (self.request_id, msg))
                                        self.messages.append((u'info', msg))
                                        instance.update()
                                        if instance.state == 'running':
                                            break
                                    except Exception, e:
                                        log.exception(u'[%s] EXCEPTION' % (self.request_id,))
                                        msg = u'%s' % (e,)
                                        self.messages.append((u'error', msg))
                                    finally:
                                        time.sleep(1)
                                        elapsed_time = time.time() - start_time
                                        if elapsed_time > settings.AWS_EC2_INSTANCE_STATE_CHECK_TIMEOUT:
                                            msg = u'Gave up trying to wait for EC2 instance to run.'
                                            log.error(u'[%s] %s' % (self.request_id, msg))
                                            self.errors.append(msg)
                                            self.messages.append((u'info', msg))
                                            break

                            if no_ec2 or (instance.state == 'running'):
                                if not no_ec2:
                                    msg = u'EC2 instance running.'
                                    log.info(u'[%s] %s]' % (self.request_id, msg))
                                    self.messages.append((u'success', msg))
                                    host = instance.public_dns_name
                                    log.debug(u'[%s] instance.public_dns_name=%s' % (self.request_id, host))
                                else:
                                    host = None

                                mysql_conn = self.create_aws_mysql_connection(host=host, wait=True)
                                if mysql_conn:
                                    #
                                    # Create schema if not exists
                                    #
                                    query = 'CREATE SCHEMA IF NOT EXISTS %s' % (database_schema.name,)
                                    utils.execute(mysql_conn, query)
                                    msg = u"Database schema '%s' was created (if not existed)." % (database_schema.name,)
                                    log.debug(u'[%s] %s' % (self.request_id, msg))
                                    self.messages.append((u'info', msg))
                                    mysql_conn.close()

                                    # Reconnect again using the newly created schema.
                                    conn_opts = {}
                                    if settings.AWS_MYSQL_HOST:
                                        conn_opts['host'] = settings.AWS_MYSQL_HOST
                                    elif host:
                                        conn_opts['host'] = host
                                    if settings.AWS_MYSQL_PORT:
                                        conn_opts['port'] = settings.AWS_MYSQL_PORT
                                    if settings.AWS_MYSQL_USER:
                                        conn_opts['user'] = settings.AWS_MYSQL_USER
                                    if settings.AWS_MYSQL_PASSWORD:
                                        conn_opts['passwd'] = settings.AWS_MYSQL_PASSWORD
                                    conn_opts['db'] = database_schema.name
                                    mysql_conn = self.create_aws_mysql_connection(
                                        db=database_schema.name, host=host)

                                    changeset_has_errors = False
                                    #validation_results = []
                                    created_changeset_test_ids = []
                                    try:
                                        #
                                        # Execute schema_version.ddl
                                        #
                                        msg = u'Executing schema version DDL.'
                                        log.info(u'[%s] %s' % (self.request_id, msg))
                                        self.messages.append((u'info', msg))
                                        #utils.execute(mysql_conn, schema_version.ddl)
                                        ddls = sqlparse.split(schema_version.ddl)
                                        for ddl in ddls:
                                            cur = None
                                            try:
                                                ddl = ddl.rstrip().rstrip(u';').rstrip().strip()
                                                log.debug(ddl)
                                                cur = mysql_conn.cursor()
                                                if ddl:
                                                    cur.execute(ddl)
                                            except Exception, e:
                                                log.exception(u'[%s] EXCEPTION' % (self.request_id,))
                                                msg = u'%s' % (e,)
                                                self.errors.append(msg)
                                                self.messages.append((u'error', msg))
                                                #validation_results.append(u'ERROR: %s' % (e,))
                                                changeset_has_errors = True
                                            finally:
                                                if cur:
                                                    cur.close()

                                        #
                                        # Apply all changeset details.
                                        #
                                        first_run = True
                                        for changeset_detail in changeset.changeset_details.select_related().order_by('id'):
                                            if first_run:
                                                # initial before structure and checksum should be the same with schema version
                                                structure_before = schema_version.ddl
                                                hash_before = schema_version.checksum
                                                structure_after = structure_before
                                                hash_after = hash_before
                                                first_run = False
                                                log.debug('Structure=\n%s\nChecksum=%s' % (structure_before, hash_before))
                                            else:
                                                # for succeeding runs, before structure and checksum is equal
                                                # to after structure and checksum of the preceeding operation
                                                structure_before = structure_after
                                                hash_before = hash_after
                                                structure_after = structure_before
                                                hash_after = hash_before

                                            msg = u'Validating changeset detail...\nid: %s\napply_sql:\n%s' % (
                                                changeset_detail.id, changeset_detail.apply_sql)
                                            log.info(u'[%s] %s' % (self.request_id, msg))
                                            self.messages.append((u'info', msg))
                                            started_at = timezone.now()
                                            cur = None
                                            results_log_items = []
                                            try:
                                                cur = mysql_conn.cursor()
                                                #affected_rows = cur.execute(changeset_detail.apply_sql)
                                                ddls = sqlparse.split(changeset_detail.apply_sql)
                                                for ddl in ddls:
                                                    ddl = ddl.rstrip().rstrip(u';').rstrip().strip()
                                                    log.debug(ddl)
                                                    if ddl:
                                                        cur.execute(ddl)
                                                        while cur.nextset() is not None:
                                                            pass

                                                #if cur.messages:
                                                #    for exc, val in cur.messages:
                                                #        val_str = u'ERROR: %s' % (val,)
                                                #        if val_str not in results_log_items:
                                                #            results_log_items.append(val_str)

                                                #structure_after = utils.dump_structure(mysql_conn)
                                                structure_after = utils.mysql_dump(**conn_opts)
                                                hash_after = utils.hash_string(structure_after)
                                                log.debug('Structure=\n%s\nChecksum=%s' % (structure_after, hash_after))

                                                # Test revert_sql
                                                ddls = sqlparse.split(changeset_detail.revert_sql)
                                                for ddl in ddls:
                                                    ddl = ddl.rstrip().rstrip(u';').rstrip().strip()
                                                    log.debug(ddl)
                                                    if ddl:
                                                        cur.execute(ddl)
                                                        while cur.nextset() is not None:
                                                            pass

                                                # revert_sql worked, reapply appy sql again
                                                ddls = sqlparse.split(changeset_detail.apply_sql)
                                                for ddl in ddls:
                                                    ddl = ddl.rstrip().rstrip(u';').rstrip().strip()
                                                    log.debug(ddl)
                                                    if ddl:
                                                        cur.execute(ddl)
                                                        while cur.nextset() is not None:
                                                            pass

                                                changeset_detail.before_checksum = hash_before
                                                changeset_detail.after_checksum = hash_after
                                                changeset_detail.save()
                                            except Exception, e:
                                                log.exception(u'[%s] EXCEPTION' % (self.request_id,))
                                                msg = u'%s' % (e,)
                                                self.errors.append(msg)
                                                self.messages.append((u'error', msg))
                                                if cur:
                                                    if cur.messages:
                                                        log.error(u'[%s] %s' % (self.request_id, cur.messages))
                                                        for exc, val in cur.messages:
                                                            val_str = u'ERROR: %s' % (val,)
                                                            if val_str not in results_log_items:
                                                                results_log_items.append(val_str)
                                                #validation_results.append(u'ERROR: %s' % (e,))
                                                changeset_has_errors = True
                                            finally:
                                                if cur:
                                                    while cur.nextset() is not None:
                                                        pass
                                                    cur.close()

                                            ended_at = timezone.now()
                                            results_log = u'\n'.join(results_log_items)
                                            test_type = models.TestType.objects.get_syntax_test_type()
                                            changeset_test = models.ChangesetTest.objects.create(
                                                changeset_detail=changeset_detail,
                                                test_type=test_type,
                                                started_at=started_at,
                                                ended_at=ended_at,
                                                results_log=results_log)
                                            created_changeset_test_ids.append(changeset_test.id)
                                            self.changeset_tests.append(changeset_test)

                                    except Exception, e:
                                        log.exception(u'[%s] EXCEPTION' % (self.request_id,))
                                        msg = u'%s' % (e,)
                                        self.errors.append(msg)
                                        self.messages.append((u'error', msg))
                                        #validation_results.append(u'ERROR: %s' % (e,))
                                        changeset_has_errors = True

                                    finally:
                                        mysql_conn.close()

                                    msg = u'Changeset syntax test was completed.'
                                    log.info(u'[%s] %s' % (self.request_id, msg))
                                    self.messages.append((u'info', msg))
                                else:
                                    msg = u'Unable to connect to MySQL server on EC2 instance.'
                                    log.error(u'[%s] %s' % (self.request_id, msg))
                                    raise Exception(msg)
                            else:
                                msg = u"Instance state did not reach 'running' state after checking for %s times." % (tries,)
                                log.error(u'[%s] %s' % (self.request_id, msg))
                                raise Exception(msg)

                        else:
                            msg = u'No EC2 instances were returned.'
                            log.warn(u'[%s] %s' % (self.request_id, msg))
                            raise Exception(msg)
                    finally:
                        if not no_ec2:
                            if instances:
                                for instance in instances:
                                    instance.terminate()
                                    msg = u'EC2 instance terminated.'
                                    log.info(u'[%s] %s' % (self.request_id, msg))
                                    self.messages.append((u'info', msg))
                else:
                    msg = u'No AWS reservation was returned.'
                    raise Exception(msg)

                msg = u'Syntax validation completed'
                self.messages.append((u'info', msg))
                log.info(u'[%s] %s' % (self.request_id, msg))

                msg = u'Starting no update with WHERE clause validation...'
                self.messages.append((u'info', msg))
                log.info(u'[%s] %s' % (self.request_id, msg))

                results = changeset_validate_no_update_with_where_clause(
                    self.changeset, self.user, server=self.server)
                if results['changeset_has_errors']:
                    changeset_has_errors = True
                if results['changeset_validation']:
                    self.changeset_validations.append(results['changeset_validation'])
                #self.changeset_tests.extend(results['changeset_tests'])

                msg = u'No update with WHERE clause validation completed'
                self.messages.append((u'info', msg))
                log.info(u'[%s] %s' % (self.request_id, msg))

                #
                # Update changeset.
                #
                after_version = models.SchemaVersion.objects.create(
                    database_schema=self.schema_version.database_schema,
                    ddl=structure_after,
                    checksum=hash_after
                )
                if changeset_has_errors:
                    changeset.review_status = models.Changeset.REVIEW_STATUS_REJECTED
                else:
                    changeset.review_status = models.Changeset.REVIEW_STATUS_IN_PROGRESS
                changeset.reviewed_by = self.user
                changeset.reviewed_at = timezone.now()
                changeset.before_version = self.schema_version
                changeset.after_version = after_version
                changeset.save()
                #
                # Create entry on changeset actions.
                models.ChangesetAction.objects.create(
                    changeset=changeset,
                    type=models.ChangesetAction.TYPE_CHANGED,
                    timestamp=timezone.now())

            changeset_validation_ids_string = u','.join([str(obj.id) for obj in self.changeset_validations])
            changeset_test_ids_string = u','.join([str(obj.id) for obj in self.changeset_tests])
            site = Site.objects.get_current()
            url = reverse('schemanizer_changeset_view_review_results', args=[changeset.id])
            query_string = urllib.urlencode(dict(
                changeset_validation_ids=changeset_validation_ids_string,
                changeset_test_ids=changeset_test_ids_string))
            self.review_results_url = 'http://%s%s?%s' % (
                site.domain,
                url,
                query_string)

            log.info(u'Changeset [id=%s] was reviewed.' % (changeset.id,))
            changeset_send_reviewed_mail(changeset)

        except Exception, e:
            log.exception('EXCEPTION')
            msg = u'%s' % (e,)
            self.errors.append(msg)
            self.messages.append((u'errors', msg))

        finally:
            msg = u'Review thread ended.'
            log.info(u'[%s] %s' % (self.request_id, msg))
            self.messages.append((u'info', msg))


def user_can_apply_changeset(user, changeset):
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)
    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)

    if not changeset.pk:
        # Cannot apply unsaved changeset.
        return False

    # only approved changesets can be applied
    if changeset.review_status not in (models.Changeset.REVIEW_STATUS_APPROVED,):
        return False

    if user.role.name in (models.Role.ROLE_DEVELOPER,):
        if changeset.classification in (models.Changeset.CLASSIFICATION_LOWRISK, models.Changeset.CLASSIFICATION_PAINLESS):
            return True
    elif user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
        return True

    return False


def changeset_apply(changeset, user, server):
    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)
    if type(server) in (int, long):
        server = models.Server.objects.get(pk=server)

    if not user_can_apply_changeset(user, changeset):
        raise exceptions.NotAllowed('User is not allowed to apply changeset.')

    thread = ChangesetApplyThread(
        changeset,
        user,
        server,
        db_user=settings.AWS_MYSQL_USER,
        db_passwd=settings.AWS_MYSQL_PASSWORD,
        db_port=settings.AWS_MYSQL_PORT)
    thread.start()
    return thread


class ChangesetApplyThread(threading.Thread):

    def __init__(
            self, changeset, user, server, db_user=None, db_passwd=None,
            db_port=None):
        super(ChangesetApplyThread, self).__init__()
        self.daemon = True

        self.changeset = changeset
        self.user = user
        self.server = server
        self.db_user = db_user
        self.db_passwd = db_passwd
        self.db_port = db_port

        self.conn = None

        # list of tuples
        # tuple = (message_type, message_text)
        self.messages = []

        self.has_errors = False
        self.changeset_detail_applies = []

    def _apply_changeset_detail(self, changeset_detail):
        has_errors = False
        changeset_detail_apply = None

        queries = sqlparse.split(changeset_detail.apply_sql)
        try:
            results_logs = []
            self.messages.append(('info', changeset_detail.apply_sql))
            for query in queries:
                query = query.rstrip(string.whitespace + ';')
                cur = self.conn.cursor()
                try:
                    cur.execute(query)
                except Exception, e:
                    log.exception('EXCEPTION')
                    self.messages.append(('error', '%s' % (e,)))
                    results_logs.append('ERROR: %s' % (e,))
                    has_errors = True
                    break
                finally:
                    while cur.nextset() is not None:
                        pass
                    cur.close()
        finally:
            results_log = '\n'.join(results_logs)
            changeset_detail_apply = models.ChangesetDetailApply.objects.create(
                changeset_detail=changeset_detail,
                environment=self.server.environment,
                server=self.server,
                results_log=results_log)

        return dict(
            has_errors=has_errors,
            changeset_detail_apply=changeset_detail_apply
        )

    def _apply_changeset_details(self):
        for changeset_detail in self.changeset.changeset_details.all():
            ret = self._apply_changeset_detail(changeset_detail)
            if ret['has_errors']:
                self.has_errors = True
            self.changeset_detail_applies.append(ret['changeset_detail_apply'])

    def run(self):
        msg = 'Changeset apply thread started.'
        log.info(msg)
        self.messages.append(('info', msg))

        try:
            with transaction.commit_on_success():
                conn_opts = {}
                conn_opts['host'] = self.server.hostname
                if self.db_port:
                    conn_opts['port'] = self.db_port
                if self.db_user:
                    conn_opts['user'] = self.db_user
                if self.db_passwd:
                    conn_opts['passwd'] = self.db_passwd
                conn_opts['db'] = self.changeset.database_schema.name
                self.conn = MySQLdb.connect(**conn_opts)
                self._apply_changeset_details()
        except Exception, e:
            log.exception('EXCEPTION')
            msg = 'ERROR: %s' % (e,)
            self.messages.append(('error', msg))
            self.has_errors = True
        finally:
            if self.conn:
                self.conn.close()

        msg = 'Changeset apply thread ended.'
        log.info(msg)
        self.messages.append(('info', msg))