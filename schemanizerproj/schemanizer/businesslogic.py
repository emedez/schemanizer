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
from schemanizer.logic import (
    mail as logic_mail,
    privileges as logic_privileges)

log = logging.getLogger(__name__)


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
        logic_mail.send_mail(subject=subject, body=body, to=to)
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
        logic_mail.send_mail(subject=subject, body=body, to=to)
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


#def changeset_send_reviewed_mail(changeset):
#    """Sends reviewed changeset email to dbas."""
#    site = Site.objects.get_current()
#    changeset_url = 'http://%s%s' % (
#        site.domain,
#        reverse('schemanizer_changeset_view', args=[changeset.id]))
#    to = list(models.User.objects.values_list('email', flat=True)
#        .filter(role__name=models.Role.ROLE_DBA))
#
#    if to:
#        subject = u'Changeset reviewed'
#        body = u'The following is the URL for the changeset that was reviewed by %s: \n%s' % (
#            changeset.reviewed_by.name, changeset_url)
#        logic_mail.send_mail(subject=subject, body=body, to=to)
#        log.info(u'Reviewed changeset email sent to: %s' % (to,))
#    else:
#        log.warn(u'No email recipients.')


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
        logic_mail.send_mail(subject=subject, body=body, to=to)
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
        logic_mail.send_mail(subject=subject, body=body, to=to)
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
