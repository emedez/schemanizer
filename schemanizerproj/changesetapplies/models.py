from django.db import models
from utils import models as utils_models


class ChangesetDetailApplyManager(models.Manager):
    def get_by_schema_version_changeset(self, schema_version_id, changeset_id):
        """Returns all changeset_detail_applies filtered by schema version and changeset."""
        return self.filter(
            before_version=schema_version_id,
            changeset_detail__changeset_id=changeset_id)


class ChangesetDetailApply(utils_models.TimeStampedModel):
    changeset_detail = models.ForeignKey('changesets.ChangesetDetail')
    environment = models.ForeignKey(
        'servers.Environment', null=True, blank=True,
        related_name='environment_changeset_detail_applies')
    server = models.ForeignKey('servers.Server')
    results_log = models.TextField(blank=True)

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


class ChangesetApply(models.Model):
    changeset = models.ForeignKey('changesets.Changeset')
    server = models.ForeignKey('servers.Server')
    applied_at = models.DateTimeField()
    applied_by = models.ForeignKey(
        'users.User', db_column='applied_by', null=True, blank=True,
        default=None, on_delete=models.SET_NULL)
    results_log = models.TextField(blank=True, default='')
    success = models.BooleanField(default=False)
    task_id = models.CharField(max_length=36, blank=True, default='')
    changeset_action = models.ForeignKey('changesets.ChangesetAction')

    class Meta:
        db_table = 'changeset_applies'

    def __unicode__(self):
        return u'<ChangesetApply id=%s>' % (self.pk,)