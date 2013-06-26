"""utils models"""

from django.db import models


class TimeStampedModel(models.Model):
    """Base class for models providing created_at and updated_at fields."""

    created_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True)
    updated_at = models.DateTimeField(
        null=True, blank=True, auto_now_add=True, auto_now=True)

    class Meta:
        abstract = True
