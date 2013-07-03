from django.contrib.auth.models import User as AuthUser
from django.db import models
from model_utils import Choices
from utils import models as utils_models


class Role(utils_models.TimeStampedModel):
    ROLE_ADMIN = u'admin'
    ROLE_DBA = u'dba'
    ROLE_DEVELOPER = u'developer'
    ROLE_LIST = [ROLE_ADMIN, ROLE_DBA, ROLE_DEVELOPER]

    NAME = Choices('admin', 'dba', 'developer')

    name = models.CharField(
        choices=NAME, default=NAME.developer, max_length=255)

    class Meta:
        db_table = 'roles'

    def __unicode__(self):
        return self.name


class User(utils_models.TimeStampedModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    role = models.ForeignKey(Role)
    github_login = models.CharField(max_length=255, null=True, blank=True)

    auth_user = models.OneToOneField(AuthUser, related_name='schemanizer_user')

    class Meta:
        db_table = 'users'

    def __unicode__(self):
        return self.name