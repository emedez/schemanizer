import logging
import string
import threading
import time
import urllib
import warnings

import MySQLdb
#warnings.filterwarnings('ignore', category=MySQLdb.Warning)

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


#def changeset_can_be_soft_deleted_by_user(changeset, user):
#    """Checks if the changeset can be soft deleted by user."""
#
#    if type(changeset) in (int, long):
#        changeset = models.Changeset.objects.get(pk=changeset)
#    if type(user) in (int, long):
#        user = models.User.objects.get(pk=user)
#
#    if not changeset.pk:
#        # Cannot soft delete unsaved changeset.
#        return False
#
#    if changeset.is_deleted:
#        # Cannot soft delete that was already soft deleted.
#        return False
#
#    if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
#        # dbas and admins can soft delete changeset
#        return True
#
#    if user.role.name in (models.Role.ROLE_DEVELOPER,):
#        if changeset.review_status != models.Changeset.REVIEW_STATUS_APPROVED:
#            # developers can only soft delete changesets that were not yet approved
#            return True
#
#    return False


def soft_delete_changeset(changeset, user):
    """Soft deletes changeset."""

    changeset = utils.get_model_instance(changeset, models.Changeset)
    user = utils.get_model_instance(user, models.User)

    logic_privileges.UserPrivileges(user).check_soft_delete_changeset(changeset)

    with transaction.commit_on_success():
        changeset.is_deleted = 1
        changeset.save()

        models.ChangesetAction.objects.create(
            changeset=changeset,
            type=models.ChangesetAction.TYPE_DELETED,
            timestamp=timezone.now()
        )

    log.info('Changeset was soft deleted, id=%s.' % (changeset.id,))

    return changeset


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

    log.info(u'A changeset was submitted, id=%s.' % (changeset.id,))
    logic_mail.send_changeset_submitted_mail(changeset)

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

    logic_mail.send_changeset_submitted_mail(changeset)
    log.info(u'A changeset was submitted, id=%s.' % (changeset.id,))

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

        logic_mail.send_changeset_updated_mail(changeset)

    else:
        raise exceptions.PrivilegeError(
            u'User is not allowed to update changeset.')

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

        logic_mail.send_changeset_updated_mail(changeset)

        return changeset
    else:
        raise exceptions.PrivilegeError(
            'User is not allowed to update changeset.')


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
                type=models.ChangesetAction.TYPE_APPROVED,
                timestamp=now)

        log.info(u'Changeset [id=%s] was approved.' % (changeset.id,))

        logic_mail.send_changeset_approved_mail(changeset)

        return changeset

    else:
        raise exceptions.PrivilegeError(
            u'User is not allowed to approve changeset.')


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
                type=models.ChangesetAction.TYPE_REJECTED,
                timestamp=now)

        log.info(u'Changeset [id=%s] was rejected.' % (changeset.id,))

        logic_mail.send_changeset_rejected_mail(changeset)

        return changeset

    else:
        log.debug(u'changeset:\n%s\n\nuser=%s' % (changeset, user.name))
        raise exceptions.PrivilegeError(
            u'User is not allowed to reject changeset.')


def save_schema_dump(server, database_schema_name, user):
    """Creates database schema (if needed) and schema version."""

    server = utils.get_model_instance(server, models.Server)
    user = utils.get_model_instance(user, models.User)

    logic_privileges.UserPrivileges(user).check_save_schema_dump()

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
        database_schema, __ = models.DatabaseSchema.objects.get_or_create(
            name=database_schema_name)
        schema_version = models.SchemaVersion.objects.create(
            database_schema=database_schema, ddl=structure,
            checksum=utils.schema_hash(structure))

    return schema_version
