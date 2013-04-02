import logging

from django.contrib.auth import get_user_model
from django.db import models

log = logging.getLogger(__name__)


class Role(models.Model):
    name = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = 'roles'

    def __unicode__(self):
        return self.name


class User(models.Model):
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(max_length=255, blank=True)
    role = models.OneToOneField(Role, db_column='role_id', null=True, blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    user = models.OneToOneField(
        get_user_model(), related_name='schemanizer_user',
        db_column='auth_user_id')

    class Meta:
        db_table = 'users'

    def __unicode__(self):
        return self.name


class Changeset(models.Model):
    DDL_TABLE_CREATE = u'DDL:Table:Create'
    DDL_TABLE_ALTER = u'DDL:Table:Alter'
    DDL_TABLE_DROP = u'DDL:Table:Drop'
    DDL_CODE_CREATE = u'DDL:Code:Create'
    DDL_CODE_ALTER = u'DDL:Code:Alter'
    DDL_CODE_DROP = u'DDL:Code:Drop'
    DML_INSERT = u'DML:Insert'
    DML_INSERT_SELECT = u'DML:Insert:Select'
    DML_UPDATE = u'DML:Update'
    DML_DELETE = u'DML:Delete'

    TYPE_CHOICES = (
        (DDL_TABLE_CREATE, DDL_TABLE_CREATE),
        (DDL_TABLE_ALTER, DDL_TABLE_ALTER),
        (DDL_TABLE_DROP, DDL_TABLE_DROP),
        (DDL_CODE_CREATE, DDL_CODE_CREATE),
        (DDL_CODE_ALTER, DDL_CODE_ALTER),
        (DDL_CODE_DROP, DDL_CODE_DROP),
        (DML_INSERT, DML_INSERT),
        (DML_INSERT_SELECT, DML_INSERT_SELECT),
        (DML_UPDATE, DML_UPDATE),
        (DML_DELETE, DML_DELETE),
    )

    CLASSIFICATION_PAINLESS = u'painless'
    CLASSIFICATION_LOWRISK = u'lowrisk'
    CLASSIFICATION_DEPENDENCY = u'dependency'
    CLASSIFICATION_IMPACTING = u'impacting'

    CLASSIFICATION_CHOICES = (
        (CLASSIFICATION_PAINLESS, CLASSIFICATION_PAINLESS),
        (CLASSIFICATION_LOWRISK, CLASSIFICATION_LOWRISK),
        (CLASSIFICATION_DEPENDENCY, CLASSIFICATION_DEPENDENCY),
        (CLASSIFICATION_IMPACTING, CLASSIFICATION_IMPACTING)
    )

    REVIEW_STATUS_NEEDS = u'needs'
    REVIEW_STATUS_IN_PROGRESS = u'in_progress'
    REVIEW_STATUS_REJECTED = u'rejected'
    REVIEW_STATUS_APPROVED = u'approved'

    REVIEW_STATUS_CHOICES = (
        (REVIEW_STATUS_NEEDS, REVIEW_STATUS_NEEDS),
        (REVIEW_STATUS_IN_PROGRESS, REVIEW_STATUS_IN_PROGRESS),
        (REVIEW_STATUS_REJECTED, REVIEW_STATUS_REJECTED),
        (REVIEW_STATUS_APPROVED, REVIEW_STATUS_APPROVED)
    )

    type = models.CharField(
        max_length=17, blank=True, choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0])
    classification = models.CharField(
        max_length=10, blank=True, choices=CLASSIFICATION_CHOICES,
        default=CLASSIFICATION_CHOICES[0][0])
    version_control_url = models.CharField(max_length=255, blank=True)
    review_status = models.CharField(
        max_length=11, blank=True, choices=REVIEW_STATUS_CHOICES,
        default=REVIEW_STATUS_CHOICES[0][0])

    reviewed_by = models.ForeignKey(
        User, db_column='reviewed_by', null=True, blank=True,
        related_name='reviewed_changesets')
    reviewed_at = models.DateTimeField(null=True, blank=True)

    approved_by = models.ForeignKey(
        User, db_column='approved_by', null=True, blank=True,
        related_name='approved_changesets')
    approved_at = models.DateTimeField(null=True, blank=True)

    submitted_by = models.ForeignKey(
        User, db_column='submitted_by', null=True, blank=True,
        related_name='submitted_changesets')
    submitted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = 'changesets'

    def __unicode__(self):
        ret = u''
        for k, v in vars(self).iteritems():
            if not k.startswith('_'):
                if ret:
                    ret += u', '
                ret += u'%s=%s' % (k, v)
        return ret


class ChangesetDetail(models.Model):
    TYPE_ADD = u'add'
    TYPE_DROP = u'drop'
    TYPE_CHANGE = u'change'
    TYPE_UPD = u'upd'
    TYPE_INS = u'ins'
    TYPE_DEL = u'del'

    TYPE_CHOICES = (
        (TYPE_ADD, TYPE_ADD),
        (TYPE_DROP, TYPE_DROP),
        (TYPE_CHANGE, TYPE_CHANGE),
        (TYPE_UPD, TYPE_UPD),
        (TYPE_INS, TYPE_INS),
        (TYPE_DEL, TYPE_DEL)
    )

    changeset = models.ForeignKey(
        Changeset, db_column='changeset_id', null=True, blank=True)
    type = models.CharField(
        max_length=6, blank=True, choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0])
    description = models.TextField(blank=True)
    apply_sql = models.TextField(blank=True)
    revert_sql = models.TextField(blank=True)
    before_checksum = models.CharField(max_length=255, blank=True)
    after_checksum = models.CharField(max_length=255, blank=True)
    count_sql = models.TextField(blank=True)
    volumetric_values = models.TextField(blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = 'changeset_details'

    def __unicode__(self):
        ret = u''
        for k, v in vars(self).iteritems():
            if not k.startswith('_'):
                if ret:
                    ret += u', '
                ret += u'%s=%s' % (k, v)
        return ret


class ChangesetAction(models.Model):
    TYPE_NEW = u'new'
    TYPE_REVISE = u'review'
    TYPE_REMOVE = u'remove'

    TYPE_CHOICES = (
        (TYPE_NEW, TYPE_NEW),
        (TYPE_REVISE, TYPE_REVISE),
        (TYPE_REMOVE, TYPE_REMOVE)
    )

    changeset = models.ForeignKey(
        Changeset, db_column='changeset_id', null=True, blank=True)
    type = models.CharField(
        max_length=6, blank=True, choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0])
    timestamp = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = 'changeset_actions'

    def __unicode__(self):
        ret = u''
        for k, v in vars(self).iteritems():
            if not k.startswith('_'):
                if ret:
                    ret += u', '
                ret += u'%s=%s' % (k, v)
        return ret