import logging
from django.db import models
from users.models import User

log = logging.getLogger(__name__)


class ChangesetManager(models.Manager):

    def get_not_deleted(self):
        return self.filter(is_deleted=0)

    def get_needs_review(self):
        return self.get_not_deleted().filter(review_status=Changeset.REVIEW_STATUS_NEEDS)


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

    database_schema = models.ForeignKey(
        'schemaversions.DatabaseSchema', db_column='database_schema_id', null=True, blank=True,
        related_name='changesets')

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

    is_deleted = models.IntegerField(null=True, blank=True, default=0)

    before_version = models.ForeignKey(
        'schemaversions.SchemaVersion', db_column='before_version', null=True,
        blank=True, related_name='+', default=None
    )
    after_version = models.ForeignKey(
        'schemaversions.SchemaVersion', db_column='after_version', null=True,
        blank=True, related_name='+', default=None
    )

    repo_filename = models.TextField(
        db_column='repo_filename', null=True, blank=True, default=None)

    objects = ChangesetManager()

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
    changeset = models.ForeignKey(
        Changeset, db_column='changeset_id', null=True, blank=True,
        related_name='changeset_details')
    description = models.TextField(blank=True)
    apply_sql = models.TextField(blank=True)
    revert_sql = models.TextField(blank=True)
    before_checksum = models.CharField(max_length=255, blank=True)
    after_checksum = models.CharField(max_length=255, blank=True)
    apply_verification_sql = models.TextField(blank=True)
    revert_verification_sql = models.TextField(
        null=True, blank=True, default=None)
    volumetric_values = models.TextField(blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    CHANGESET_TEST_STATUS_NONE = 0
    CHANGESET_TEST_STATUS_SUCCESS = 1
    CHANGESET_TEST_STATUS_FAILED = 2

    class Meta:
        db_table = 'changeset_details'

    def __unicode__(self):
        return u'<ChangesetDetail id=%s>' % (self.pk,)

    def changeset_test_status(self):
        """Returns changeset test status."""

        changeset_tests = ChangesetTest.objects.filter(changeset_detail=self)
        if not changeset_tests.exists():
            return ChangesetDetail.CHANGESET_TEST_STATUS_NONE
        status = ChangesetDetail.CHANGESET_TEST_STATUS_SUCCESS
        for changeset_test in changeset_tests:
            if changeset_test.results_log and changeset_test.results_log.strip():
                # results log, if not empty contains the error message
                status = ChangesetDetail.CHANGESET_TEST_STATUS_FAILED
                break
        return status


class ChangesetAction(models.Model):
    TYPE_CREATED = u'created'
    TYPE_CREATED_WITH_DATA_FROM_GITHUB_REPO = u'created with data from github repo'
    TYPE_CHANGED = u'changed'
    TYPE_CHANGED_WITH_DATA_FROM_GITHUB_REPO = u'changed with data from github repo'
    TYPE_DELETED = u'deleted'
    TYPE_REVIEW_STARTED = u'review started'
    TYPE_REVIEWED = u'reviewed'
    TYPE_VALIDATIONS_PASSED = u'validations passed'
    TYPE_VALIDATIONS_FAILED = u'validations failed'
    TYPE_TESTS_PASSED = u'tests passed'
    TYPE_TESTS_FAILED = u'tests failed'
    TYPE_APPROVED = u'approved'
    TYPE_REJECTED = u'rejected'
    TYPE_APPLIED = u'applied'
    TYPE_APPLIED_FAILED = u'applied - failed'

    TYPE_CHOICES = (
        (TYPE_CREATED, TYPE_CREATED),
        (
            TYPE_CREATED_WITH_DATA_FROM_GITHUB_REPO,
            TYPE_CREATED_WITH_DATA_FROM_GITHUB_REPO),
        (TYPE_CHANGED, TYPE_CHANGED),
        (
            TYPE_CHANGED_WITH_DATA_FROM_GITHUB_REPO,
            TYPE_CHANGED_WITH_DATA_FROM_GITHUB_REPO),
        (TYPE_DELETED, TYPE_DELETED),
        (TYPE_REVIEW_STARTED, TYPE_REVIEW_STARTED),
        (TYPE_REVIEWED, TYPE_REVIEWED),
        (TYPE_VALIDATIONS_PASSED, TYPE_VALIDATIONS_PASSED),
        (TYPE_VALIDATIONS_FAILED, TYPE_VALIDATIONS_FAILED),
        (TYPE_TESTS_PASSED, TYPE_TESTS_PASSED),
        (TYPE_TESTS_FAILED, TYPE_TESTS_FAILED),
        (TYPE_APPROVED, TYPE_APPROVED),
        (TYPE_REJECTED, TYPE_REJECTED),
        (TYPE_APPLIED, TYPE_APPLIED),
        (TYPE_APPLIED_FAILED, TYPE_APPLIED_FAILED),
    )

    changeset = models.ForeignKey(
        Changeset, db_column='changeset_id', null=True, blank=True)
    type = models.CharField(
        max_length=34, null=True, blank=True, choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0])
    timestamp = models.DateTimeField(null=True, blank=True)

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


class ChangesetDetailApplyManager(models.Manager):
    def get_by_schema_version_changeset(self, schema_version_id, changeset_id):
        """Returns all changeset_detail_applies filtered by schema version and changeset."""
        return self.filter(
            before_version=schema_version_id,
            changeset_detail__changeset_id=changeset_id)


class ChangesetDetailApply(models.Model):
    changeset_detail = models.ForeignKey(
        ChangesetDetail, db_column='changeset_detail_id', null=True, blank=True,
        related_name='changeset_detail_applies')
    #before_version = models.IntegerField(null=True, blank=True)
    #after_version = models.IntegerField(null=True, blank=True)
    environment = models.ForeignKey(
        'servers.Environment', null=True, blank=True,
        related_name='environment_changeset_detail_applies')
    server = models.ForeignKey(
        'servers.Server', null=True, blank=True,
        related_name='server_changeset_detail_applies')
    results_log = models.TextField(blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    objects = ChangesetDetailApplyManager()

    class Meta:
        db_table = 'changeset_detail_applies'
        verbose_name_plural = 'changeset detail applies'

    def __unicode__(self):
        ret = u''
        for k, v in vars(self).iteritems():
            if not k.startswith('_'):
                if ret:
                    ret += u', '
                ret += u'%s=%s' % (k, v)
        return ret


class ValidationType(models.Model):
    name = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    validation_commands = models.TextField(blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = 'validation_types'

    def __unicode__(self):
        return u'%s' % (self.name,)


class ChangesetValidation(models.Model):
    changeset = models.ForeignKey(
        Changeset, db_column='changeset_id', null=True, blank=True)
    validation_type = models.ForeignKey(
        ValidationType, db_column='validation_type_id', null=True, blank=True)
    timestamp = models.DateTimeField(null=True, blank=True)
    result = models.TextField(blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = 'changeset_validations'

    def has_errors(self):
        if self.result and self.result.strip():
            return True
        else:
            return False


class TestTypeManager(models.Manager):
    def get_syntax_test_type(self):
        return self.get(name=u'syntax')


class TestType(models.Model):
    name = models.CharField(max_length=255L, blank=True)
    description = models.TextField(blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    objects = TestTypeManager()

    class Meta:
        db_table = 'test_types'

    def __unicode__(self):
        return self.name


class ChangesetTest(models.Model):
    changeset_detail = models.ForeignKey(
        ChangesetDetail, db_column='changeset_detail_id', null=True, blank=True)
    test_type = models.ForeignKey(
        TestType, db_column='test_type_id', null=True, blank=True)
    environment = models.ForeignKey(
        'servers.Environment', null=True, blank=True)
    server = models.ForeignKey(
        'servers.Server', null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    results_log = models.TextField(blank=True)

    created_at = models.DateTimeField(null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = 'changeset_tests'

    def __unicode__(self):
        return u'<ChangesetTest id=%s>' % (self.pk,)

    def has_errors(self):
        if self.results_log and self.results_log.strip():
            return True
        else:
            return False


class ChangesetReview(models.Model):
    """Result and other related info about a changeset review."""

    changeset = models.OneToOneField(
        Changeset, db_column='changeset_id', null=True, blank=True,
        default=None)
    results_log = models.TextField(null=True, blank=True, default=None)
    success = models.BooleanField(default=False)
    task_id = models.CharField(
        max_length=36, null=True, blank=True, default=None)
    created_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        db_table = 'changeset_reviews'

    def __unicode__(self):
        return u'<ChangesetReview id=%s>' % (self.pk,)


class ChangesetApply(models.Model):
    changeset = models.ForeignKey(
        Changeset, db_column='changeset_id', null=True, blank=True,
        default=None)
    server = models.ForeignKey(
        'servers.Server', null=True, blank=True, default=None)
    applied_at = models.DateTimeField(null=True, blank=True)
    applied_by = models.ForeignKey(
        User, db_column='applied_by', null=True, blank=True, default=None)
    results_log = models.TextField(null=True, blank=True, default=None)
    success = models.BooleanField(default=False)
    task_id = models.CharField(
        max_length=36, null=True, blank=True, default=None)
    changeset_action = models.ForeignKey(
        ChangesetAction, db_column='changeset_action_id', null=True,
        blank=True, default=None)

    class Meta:
        db_table = 'changeset_applies'

    def __unicode__(self):
        return u'<ChangesetApply id=%s>' % (self.pk,)


class ChangesetActionServerMap(models.Model):
    changeset_action = models.ForeignKey(
        ChangesetAction, db_column='changeset_action_id', null=True,
        blank=True, default=None)
    server = models.ForeignKey(
        'servers.Server', null=True, blank=True, default=None)

    class Meta:
        db_table = 'changeset_action_server_map'

    def __unicode__(self):
        changeset_action_id = None
        if self.changeset_action:
            changeset_action_id = self.changeset_action.id
        server_id = None
        if self.server:
            server_id = self.server.id
        return (
            u'<ChangesetActionServerMap: changeset_action.id=%s, '
            u'server.id=%s>' % (changeset_action_id, server_id))
