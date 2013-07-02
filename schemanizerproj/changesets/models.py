from django.db import models
from utils import models as utils_models
from changesettests import models as changesettests_models


class NotDeletedChangesetManager(models.Manager):
    def get_query_set(self):
        return super(NotDeletedChangesetManager, self).get_query_set().filter(
            is_deleted=False)


class ToBeReviewedChangesetManager(models.Manager):
    def get_query_set(self):
        return super(ToBeReviewedChangesetManager, self).get_query_set().filter(
            is_deleted=False,
            review_status=Changeset.REVIEW_STATUS_NEEDS)


class Changeset(utils_models.TimeStampedModel):
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

    database_schema = models.ForeignKey('schemaversions.DatabaseSchema')
    type = models.CharField(
        max_length=17, choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0])
    classification = models.CharField(
        max_length=10, choices=CLASSIFICATION_CHOICES,
        default=CLASSIFICATION_CHOICES[0][0])
    version_control_url = models.CharField(max_length=255, blank=True)
    review_status = models.CharField(
        max_length=11, blank=True, choices=REVIEW_STATUS_CHOICES,
        default=REVIEW_STATUS_CHOICES[0][0])
    reviewed_by = models.ForeignKey(
        'users.User', db_column='reviewed_by', null=True, blank=True,
        default=None, on_delete=models.SET_NULL, related_name='+')
    reviewed_at = models.DateTimeField(null=True, blank=True, default=None)
    approved_by = models.ForeignKey(
        'users.User', db_column='approved_by', null=True, blank=True,
        default=None, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True, default=None)
    submitted_by = models.ForeignKey(
        'users.User', db_column='submitted_by', null=True, blank=True,
        default=None, on_delete=models.SET_NULL, related_name='+')
    submitted_at = models.DateTimeField(null=True, blank=True, default=None)
    is_deleted = models.BooleanField(default=False)
    review_version = models.ForeignKey(
        'schemaversions.SchemaVersion', db_column='review_version',
        null=True, default=None, on_delete=models.SET_NULL, related_name='+',
        help_text='Target schema version when running a changeset review.')
    before_version = models.ForeignKey(
        'schemaversions.SchemaVersion', db_column='before_version', null=True,
        blank=True, default=None, on_delete=models.SET_NULL, related_name='+')
    after_version = models.ForeignKey(
        'schemaversions.SchemaVersion', db_column='after_version', null=True,
        blank=True, default=None, on_delete=models.SET_NULL, related_name='+')
    repo_filename = models.TextField(blank=True, default='')

    objects = models.Manager()
    not_deleted_objects = NotDeletedChangesetManager()
    to_be_reviewed_objects = ToBeReviewedChangesetManager()

    class Meta:
        db_table = 'changesets'

    def __unicode__(self):
        return u'Changeset [id=%s]' % self.pk

    def clean(self):
        from django.core.exceptions import ValidationError
        database_schema = None
        try:
            database_schema = self.database_schema
        except:
            pass
        review_version = None
        try:
            review_version = self.review_version
        except:
            pass
        if database_schema and review_version:
            if database_schema.pk != review_version.database_schema.pk:
                raise ValidationError(
                    'Invalid schema version, it should be related to the '
                    'selected database schema.')


class ChangesetDetail(utils_models.TimeStampedModel):
    changeset = models.ForeignKey(Changeset)
    description = models.TextField(blank=True, default='')
    apply_sql = models.TextField(blank=True, default='')
    revert_sql = models.TextField(blank=True, default='')
    before_checksum = models.CharField(max_length=255, blank=True, default='')
    after_checksum = models.CharField(max_length=255, blank=True, default='')
    apply_verification_sql = models.TextField(blank=True, default='')
    revert_verification_sql = models.TextField(blank=True, default='')
    volumetric_values = models.TextField(blank=True, default='')

    CHANGESET_TEST_STATUS_NONE = 0
    CHANGESET_TEST_STATUS_SUCCESS = 1
    CHANGESET_TEST_STATUS_FAILED = 2

    class Meta:
        db_table = 'changeset_details'

    def __unicode__(self):
        return u'ChangesetDetail [id=%s]' % self.pk

    def changeset_test_status(self):
        """Returns changeset test status."""

        changeset_tests = changesettests_models.ChangesetTest.objects.filter(
            changeset_detail=self)
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

    changeset = models.ForeignKey(Changeset)
    type = models.CharField(
        max_length=34, null=True, blank=True, choices=TYPE_CHOICES,
        default=TYPE_CHOICES[0][0])
    timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'changeset_actions'

    def __unicode__(self):
        return u'ChangesetAction [id=%s]' % self.pk


class ChangesetActionServerMap(models.Model):
    changeset_action = models.ForeignKey(ChangesetAction)
    server = models.ForeignKey('servers.Server')

    class Meta:
        db_table = 'changeset_action_server_map'

    def __unicode__(self):
        return u'ChangesetActionServerMap [id=%s]' % self.pk
