import json
import logging
from pprint import pprint as pp

from django.conf.urls import url
from django.contrib.auth.models import User as AuthUser

from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields

from schemanizer import models, businesslogic

log = logging.getLogger(__name__)


class AuthUserResource(ModelResource):
    class Meta:
        queryset = AuthUser.objects.all()
        resource_name = 'auth_user'
        fields = ['username', 'first_name', 'last_name', 'last_login']
        authentication = BasicAuthentication()
        authorization = Authorization()


class RoleResource(ModelResource):
    class Meta:
        queryset = models.Role.objects.all()
        resource_name = 'role'
        authentication = BasicAuthentication()
        authorization = Authorization()


class UserResource(ModelResource):
    auth_user = fields.ForeignKey(AuthUserResource, 'auth_user', full=True)
    role = fields.ForeignKey(RoleResource, 'role', null=True, blank=True, full=True)

    class Meta:
        queryset = models.User.objects.all()
        resource_name = 'user'
        authentication = BasicAuthentication()
        authorization = Authorization()


class DatabaseSchemaResource(ModelResource):
    class Meta:
        queryset = models.DatabaseSchema.objects.all()
        resource_name = 'database_schema'
        authentication = BasicAuthentication()
        authorization = Authorization()


class SchemaVersionResource(ModelResource):
    database_schema = fields.ForeignKey(DatabaseSchemaResource, 'database_schema', null=True, blank=True, full=True)

    class Meta:
        queryset = models.SchemaVersion.objects.all()
        resource_name = 'schema_version'
        authentication = BasicAuthentication()
        authorization = Authorization()


class ChangesetResource(ModelResource):
    database_schema = fields.ForeignKey(DatabaseSchemaResource, 'database_schema', null=True, blank=True, full=True)
    reviewed_by = fields.ForeignKey(UserResource, 'reviewed_by', null=True, blank=True, full=True)
    approved_by = fields.ForeignKey(UserResource, 'approved_by', null=True, blank=True, full=True)
    submitted_by = fields.ForeignKey(UserResource, 'submitted_by', null=True, blank=True, full=True)
    before_version = fields.ForeignKey(SchemaVersionResource, 'before_version', null=True, blank=True, full=True)
    after_version = fields.ForeignKey(SchemaVersionResource, 'after_version', null=True, blank=True, full=True)

    class Meta:
        queryset = models.Changeset.objects.all()
        resource_name = 'changeset'
        authentication = BasicAuthentication()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        authorization = Authorization()
        filtering = {
            'review_status': ALL,
        }

    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>%s)/submit/$' % (self._meta.resource_name,),
                self.wrap_view('changeset_submit'),
                name='api_changeset_submit',
            ),
            url(
                r'^(?P<resource_name>%s)/reject/(?P<changeset_id>\d+)/$' % (self._meta.resource_name,),
                self.wrap_view('changeset_reject'),
                name='api_changeset_reject',
            ),
            url(
                r'^(?P<resource_name>%s)/approve/(?P<changeset_id>\d+)/$' % (self._meta.resource_name,),
                self.wrap_view('changeset_approve'),
                name='api_changeset_approve',
            ),
        ]

    def changeset_submit(self, request, **kwargs):
        """Submits changeset.

        request.raw_post_data should be in the following form:
        {
            'changeset': {
                'database_schema': 1,
                'type': 'DDL:Table:Create',
                'classification': 'painless',
                'version_control_url': ''
            },
            'changeset_details': [
                {
                    'type': 'add',
                    'description': 'create a table',
                    'apply_sql': 'create table t1 (id int primary key auto_increment)',
                    'revert_sql': 'drop table t1'
                }
            ]
        }
        """

        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)
        self.throttle_check(request)

        try:
            data = json.loads(request.raw_post_data)
            allowed_fields = ('database_schema', 'type', 'classification', 'version_control_url')
            changeset_data = data['changeset']
            for k, v in changeset_data.iteritems():
                if k not in allowed_fields:
                    raise Exception('Changeset has invalid field \'%s\'.' % (k,))
            changeset_data['database_schema'] = models.DatabaseSchema.objects.get(pk=int(changeset_data['database_schema']))
            changeset = models.Changeset(**changeset_data)

            changeset_details_data = data['changeset_details']
            changeset_details = []
            for changeset_detail_data in changeset_details_data:
                changeset_detail = models.ChangesetDetail(**changeset_detail_data)
                changeset_details.append(changeset_detail)

            changeset = businesslogic.changeset_submit(changeset, changeset_details, request.user.schemanizer_user)
            bundle = self.build_bundle(obj=changeset, request=request)
            bundle = self.full_dehydrate(bundle)
        except:
            log.exception('EXCEPTION')
            raise

        self.log_throttled_access(request)
        return self.create_response(request, bundle)

    def changeset_reject(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)
        self.throttle_check(request)

        try:
            businesslogic.changeset_reject(int(kwargs['changeset_id']), request.user.schemanizer_user)
            bundle = self.build_bundle(request=request)
            bundle = self.full_dehydrate(bundle)
        except:
            log.exception('EXCEPTION')
            raise

        self.log_throttled_access(request)
        return self.create_response(request, bundle)

    def changeset_approve(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)
        self.throttle_check(request)

        try:
            businesslogic.changeset_approve(int(kwargs['changeset_id']), request.user.schemanizer_user)
            bundle = self.build_bundle(request=request)
            bundle = self.full_dehydrate(bundle)
        except:
            log.exception('EXCEPTION')
            raise

        self.log_throttled_access(request)
        return self.create_response(request, bundle)


class ChangesetDetailResource(ModelResource):
    changeset = fields.ForeignKey(ChangesetResource, 'changeset', null=True, blank=True, full=True)

    class Meta:
        queryset = models.ChangesetDetail.objects.all()
        resource_name = 'changeset_detail'
        authentication = BasicAuthentication()
        authorization = Authorization()

