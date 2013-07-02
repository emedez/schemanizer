from django.db import models
from utils import models as utils_models


class ChangesetReview(utils_models.TimeStampedModel):
    """Result and other related info about a changeset review."""

    changeset = models.OneToOneField('changesets.Changeset')
    schema_version = models.ForeignKey(
        'schemaversions.SchemaVersion', null=True, blank=True, default=None,
        on_delete=models.SET_NULL)
    results_log = models.TextField(blank=True, default='')
    success = models.BooleanField(default=False)
    task_id = models.CharField(max_length=36, blank=True, default=None)

    class Meta:
        db_table = 'changeset_reviews'

    def __unicode__(self):
        return u'ChangesetReview [id=%s]' % self.pk