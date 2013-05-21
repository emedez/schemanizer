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
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
from django.core.urlresolvers import reverse
from django.db import transaction

from django.utils import timezone

import boto.ec2
import sqlparse

from schemanizer import exceptions, models, utils

log = logging.getLogger(__name__)


def update_user(id, name, email, role, user):
    """Updates user."""
    role = utils.get_model_instance(role, models.Role)
    user = utils.get_model_instance(user, models.User)

    if UserPrivileges.can_update_users(user):
        with transaction.commit_on_success():
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
    else:
        raise exceptions.NotAllowed('User is now allowed to update user.')


def create_user(name, email, role, password, user):
    """Creates user."""
    role = utils.get_model_instance(role, models.Role)
    user = utils.get_model_instance(user, models.User)

    if UserPrivileges.can_create_users(user):
        with transaction.commit_on_success():
            auth_user = AuthUser.objects.create_user(name, email, password)
            schemanizer_user = models.User.objects.create(name=name, email=email, role=role, auth_user=auth_user)
        log.info(u'User [id=%s] was created.' % (schemanizer_user.id,))
        return schemanizer_user
    else:
        raise exceptions.NotAllowed('User is not allowed to create user.')


def delete_user(to_be_deleted_user, user):
    """Deletes user."""
    to_be_deleted_user = utils.get_model_instance(to_be_deleted_user, models.User)
    user = utils.get_model_instance(user, models.User)

    if UserPrivileges.can_delete_users(user):
        with transaction.commit_on_success():
            auth_user = to_be_deleted_user.auth_user
            user_id = to_be_deleted_user.id
            auth_user.delete()
        log.info(u'User [id=%s] was deleted.' % (user_id,))
    else:
        raise exceptions.NotAllowed('User is not allowed to delete user.')


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

    if changeset.is_deleted:
        # Cannot soft delete that was already soft deleted.
        return False

    if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
        # dbas and admins can soft delete changeset
        return True

    if user.role.name in (models.Role.ROLE_DEVELOPER,):
        if changeset.review_status != models.Changeset.REVIEW_STATUS_APPROVED:
            # developers can only soft delete changesets that were not yet approved
            return True

    return False


def soft_delete_changeset(changeset, user):
    """Soft deletes changeset."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if changeset_can_be_soft_deleted_by_user(changeset, user):
        changeset.is_deleted = 1
        changeset.save()

        models.ChangesetAction.objects.create(
            changeset=changeset,
            type=models.ChangesetAction.TYPE_DELETED,
            timestamp=timezone.now()
        )
        log.info('Changeset [id=%s] was soft deleted.' % (changeset.id,))

        return changeset
    else:
        raise exceptions.NotAllowed('User is not allowed to soft delete the changeset.')


def delete_changeset(changeset):
    """Deletes changeset."""

    if type(changeset) in (int, long):
        changeset = models.Changeset.objects.get(pk=changeset)

    changeset_id = changeset.id
    changeset.delete()
    log.info('Changeset [id=%s] was deleted.' % (changeset_id,))


def changeset_submit_from_form(**kwargs):
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
        timestamp=now)

    log.info(u'A changeset was submitted:\n%s' % (changeset,))

    send_changeset_submitted_mail(changeset)

    return changeset


def changeset_submit(changeset, changeset_details, user):
    if type(user) in (int, long):
        user = models.User.objects.get(pk=user)

    if changeset.pk:
        raise Exception('Only new changesets can be submitted.')

    for changeset_detail in changeset_details:
        if changeset_detail.pk:
            raise Exception('Only new changeset detail is allowed for changeset submission.')

    now = timezone.now()

    with transaction.commit_on_success():
        changeset.submitted_by = user
        changeset.submitted_at = now
        changeset.save()

        for changeset_detail in changeset_details:
            changeset_detail.changeset = changeset
            changeset_detail.save()

        models.ChangesetAction.objects.create(
            changeset=changeset,
            type=models.ChangesetAction.TYPE_CREATED,
            timestamp=now
        )

    send_changeset_submitted_mail(changeset)
    log.info('A changeset [id=%s] was submitted.' % (changeset.id,))

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


def changeset_update_from_form(**kwargs):
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


def changeset_update(changeset, changeset_details, to_be_deleted_changeset_details, user):
    user = utils.get_model_instance(user, models.User)

    if changeset_can_be_updated_by_user(changeset, user):
        with transaction.commit_on_success():
            now = timezone.now()

            for tbdc in to_be_deleted_changeset_details:
                if tbdc.pk and tbdc.changeset and tbdc.changeset.id == changeset.id:
                    tbdc.delete()
                else:
                    raise Exception('to_be_deleted_changeset_details contain and invalid changeset detail.')

            changeset.review_status = changeset.REVIEW_STATUS_NEEDS
            changeset.save()

            for cd in changeset_details:
                if cd.pk:
                    if cd.changeset.id == changeset.id:
                        cd.save()
                    else:
                        raise Exception('One of the changeset details have invalid changeset value.')
                else:
                    cd.changeset = changeset
                    cd.save()

            # Create entry on changeset actions
            models.ChangesetAction.objects.create(
                changeset=changeset,
                type=models.ChangesetAction.TYPE_CHANGED,
                timestamp=now)

        log.info(u'Changeset [id=%s] was updated.' % (changeset.id,))

        changeset_send_updated_mail(changeset)

        return changeset
    else:
        raise exceptions.NotAllowed('User is not allowed to update changeset.')


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

        return changeset

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

        return changeset

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


def normalize_mysql_dump(dump):
    statement_list = sqlparse.split(dump)
    new_statement_list = []
    for statement in statement_list:
        stripped_chars = unicode(string.whitespace + ';')
        statement = statement.strip(stripped_chars)
        if statement:
            if not statement.startswith(u'/*!'):
                # skip processing conditional comments
                new_statement_list.append(statement)
    return u';\n'.join(new_statement_list)


def schema_hash(dump):
    return utils.hash_string(normalize_mysql_dump(dump))


class UserPrivileges:
    """Encapsulates user privilege logic."""

    @classmethod
    def can_update_environments(cls, user):
        """Checks if user can update environments."""
        user = utils.get_model_instance(user, models.User)
        if user.role.name in [models.Role.ROLE_DBA, models.Role.ROLE_ADMIN]:
            return True
        else:
            return False

    @classmethod
    def can_delete_environments(cls, user):
        """Checks if user can delete environments."""
        user = utils.get_model_instance(user, models.User)
        if user.role.name in [models.Role.ROLE_DBA, models.Role.ROLE_ADMIN]:
            return True
        else:
            return False

    @classmethod
    def can_save_schema_dumps(cls, user):
        """Checks if user can save schema dumps."""
        # Everyone can save schema dumps.
        return True

    @classmethod
    def can_create_users(cls, user):
        """Checks if user can create users."""
        if user.role.name in [models.Role.ROLE_ADMIN]:
            return True
        else:
            return False

    @classmethod
    def can_update_users(cls, user):
        """Checks if user can update users."""
        if user.role.name in [models.Role.ROLE_ADMIN]:
            return True
        else:
            return False

    @classmethod
    def can_delete_users(cls, user):
        """Checks if user can delete users."""
        if user.role.name in [models.Role.ROLE_ADMIN]:
            return True
        else:
            return False


def save_schema_dump(server, database_schema_name, user):
    """Creates database schema (if needed) and schema version."""

    server = utils.get_model_instance(server, models.Server)
    user = utils.get_model_instance(user, models.User)

    if UserPrivileges.can_save_schema_dumps(user):
        conn_opts = {}
        conn_opts['host'] = server.hostname
        if server.port:
            conn_opts['port'] = server.port
        if settings.AWS_MYSQL_USER:
            conn_opts['user'] = settings.AWS_MYSQL_USER
        if settings.AWS_MYSQL_PASSWORD:
            conn_opts['passwd'] = settings.AWS_MYSQL_PASSWORD

        structure = utils.mysql_dump(database_schema_name, **conn_opts)

        with transaction.commit_on_success():
            database_schema, __ = models.DatabaseSchema.objects.get_or_create(name=database_schema_name)
            schema_version = models.SchemaVersion.objects.create(
                database_schema=database_schema,
                ddl=structure,
                checksum=schema_hash(structure))

        return schema_version
    else:
        raise exceptions.NotAllowed('User is not allowed to save schema dumps.')
