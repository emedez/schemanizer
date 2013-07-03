"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from django.utils import timezone
import factory
from schemanizer import models as schemanizer_models
from . import models
from users.models import User


class EventFactory(factory.DjangoModelFactory):
    FACTORY_FOR = models.Event

    datetime = factory.LazyAttribute(lambda obj: timezone.now())
    type = factory.Sequence(lambda n: 'type%d' % (n,))
    description = factory.Sequence(lambda n: 'description%d' % (n,))
    user = User.objects.get(name='admin')


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)
