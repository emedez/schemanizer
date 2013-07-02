from django.db import models
from utils import models as utils_models


class ValidationType(utils_models.TimeStampedModel):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    validation_commands = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'validation_types'

    def __unicode__(self):
        return u'%s' % (self.name,)


class ChangesetValidation(utils_models.TimeStampedModel):
    changeset = models.ForeignKey('changesets.Changeset')
    validation_type = models.ForeignKey('changesetvalidations.ValidationType')
    timestamp = models.DateTimeField(null=True, blank=True, default=None)
    result = models.TextField(blank=True, default='')

    class Meta:
        db_table = 'changeset_validations'

    def __unicode__(self):
        return u'ChangesetValidation [id=%s]' % self.pk

    def has_errors(self):
        if self.result and self.result.strip():
            return True
        else:
            return False