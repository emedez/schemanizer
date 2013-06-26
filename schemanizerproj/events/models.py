from django.db import models
import model_utils


class Event(models.Model):
    """Event"""
    TYPE = model_utils.Choices(
        'user_added', 'user_updated', 'user_deleted',
        'environment_added', 'environment_updated', 'environment_deleted',
        'server_added', 'server_updated', 'server_deleted',
        'schema_version_generated',
        'schema_check')

    datetime = models.DateTimeField(auto_now_add=True, blank=True)
    type = models.CharField(choices=TYPE, max_length=255)
    description = models.TextField(blank=True, default='')
    user = models.ForeignKey(
        'users.User', null=True, blank=True, default=None,
        on_delete=models.SET_NULL)

    class Meta:
        db_table = 'events'

    def __unicode__(self):
        """Returns the unicode representation of the object."""
        return u'datetime=%s, type=%s, description=%s, user=%s' % (
            self.datetime, self.type, self.description, self.user)
