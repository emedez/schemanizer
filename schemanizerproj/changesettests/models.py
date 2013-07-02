from django.db import models
from utils import models as utils_models


class TestTypeManager(models.Manager):
    def get_syntax_test_type(self):
        return self.get(name=u'syntax')


class TestType(utils_models.TimeStampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')

    objects = TestTypeManager()

    class Meta:
        db_table = 'test_types'

    def __unicode__(self):
        return self.name


class ChangesetTest(utils_models.TimeStampedModel):
    changeset_detail = models.ForeignKey('changesets.ChangesetDetail')
    test_type = models.ForeignKey('changesettests.TestType')
    environment = models.ForeignKey(
        'servers.Environment', null=True, blank=True, default=None)
    server = models.ForeignKey(
        'servers.Server', null=True, blank=True, default=None)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    results_log = models.TextField(blank=True)

    class Meta:
        db_table = 'changeset_tests'

    def __unicode__(self):
        return u'ChangesetTest [id=%s]' % self.pk

    def has_errors(self):
        if self.results_log and self.results_log.strip():
            return True
        else:
            return False


