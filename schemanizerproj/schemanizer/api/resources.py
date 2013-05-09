import json
import logging
from pprint import pprint as pp

from django.conf.urls import url
from django.contrib.auth.models import User as AuthUser

from tastypie.authentication import BasicAuthentication
from tastypie.authorization import Authorization, ReadOnlyAuthorization
from tastypie.resources import ModelResource, ALL, ALL_WITH_RELATIONS
from tastypie import fields

from schemanizer import models, businesslogic, exceptions
from schemanizer.api import authorizations

log = logging.getLogger(__name__)


class AuthUserResource(ModelResource):
    class Meta:
        queryset = AuthUser.objects.all()
        resource_name = 'auth_user'
        fields = ['username', 'first_name', 'last_name', 'last_login']
        authentication = BasicAuthentication()
        authorization = ReadOnlyAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']


class RoleResource(ModelResource):
    class Meta:
        queryset = models.Role.objects.all()
        resource_name = 'role'
        authentication = BasicAuthentication()
        authorization = ReadOnlyAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']


class UserResource(ModelResource):
    auth_user = fields.ForeignKey(AuthUserResource, 'auth_user', full=True)
    role = fields.ForeignKey(RoleResource, 'role', null=True, blank=True, full=True)

    class Meta:
        queryset = models.User.objects.all()
        resource_name = 'user'
        authentication = BasicAuthentication()
        authorization = ReadOnlyAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']

    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>%s)/create/$' % (self._meta.resource_name,),
                self.wrap_view('user_create'),
                name='api_user_create',
            ),
            url(
                r'^(?P<resource_name>%s)/update/(?P<user_id>\d+)/$' % (self._meta.resource_name,),
                self.wrap_view('user_update'),
                name='api_user_update',
            ),
            url(
                r'^(?P<resource_name>%s)/delete/(?P<user_id>\d+)/$' % (self._meta.resource_name,),
                self.wrap_view('user_delete'),
                name='api_user_delete',
            ),
        ]

    def user_create(self, request, **kwargs):
        """Creates user.

        request.raw_post_data should be in the following form:
        {
            'name': 'Pilar',
            'email': 'pilar@example.com',
            'role_id': 1,
            'password': 'secret'
        }
        """
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        user = None
        data = {}
        try:
            raw_post_data = json.loads(request.raw_post_data)
            name = raw_post_data['name']
            email = raw_post_data['email']
            role_id = int(raw_post_data['role_id'])
            password = raw_post_data['password']
            user = businesslogic.create_user(name, email, role_id, password, request.user.schemanizer_user)
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(obj=user, data=data, request=request)
        if user and user.pk:
            bundle = self.full_dehydrate(bundle)

        return self.create_response(request, bundle)

    def user_update(self, request, **kwargs):
        """Updates user.

        request.raw_post_data should be in the following form:
        {
            'name': 'Pilar',
            'email': 'pilar@example.com',
            'role': 1
        }
        """
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        user = None
        data = {}
        try:
            user_id = int(kwargs.get('user_id'))
            raw_post_data = json.loads(request.raw_post_data)
            name = raw_post_data['name']
            email = raw_post_data['email']
            role_id = int(raw_post_data['role_id'])
            user = businesslogic.update_user(user_id, name, email, role_id, request.user.schemanizer_user)
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(obj=user, data=data, request=request)
        if user and user.pk:
            bundle = self.full_dehydrate(bundle)

        return self.create_response(request, bundle)

    def user_delete(self, request, **kwargs):
        """Deletes user."""
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        user = None
        data = {}
        try:
            user_id = int(kwargs.get('user_id'))
            businesslogic.delete_user(user_id, request.user.schemanizer_user)
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(obj=user, data=data, request=request)
        if user and user.pk:
            bundle = self.full_dehydrate(bundle)

        return self.create_response(request, bundle)


class EnvironmentResource(ModelResource):
    class Meta:
        queryset = models.Environment.objects.all()
        resource_name = 'environment'
        authentication = BasicAuthentication()
        authorization = authorizations.EnvironmentAuthorization()
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'post', 'put', 'delete', 'patch']


class ServerResource(ModelResource):
    environment = fields.ForeignKey(EnvironmentResource, 'environment', full=True, null=True, blank=True)

    class Meta:
        queryset = models.Server.objects.all()
        resource_name = 'server'
        authentication = BasicAuthentication()
        authorization = Authorization()
        list_allowed_methods = ['get', 'post']
        detail_allowed_methods = ['get', 'post', 'put', 'delete', 'patch']


class DatabaseSchemaResource(ModelResource):
    class Meta:
        queryset = models.DatabaseSchema.objects.all()
        resource_name = 'database_schema'
        authentication = BasicAuthentication()
        authorization = ReadOnlyAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        filtering = {
            'id': ALL,
            'name': ALL,
        }


class SchemaVersionResource(ModelResource):
    database_schema = fields.ForeignKey(DatabaseSchemaResource, 'database_schema', null=True, blank=True, full=True)

    class Meta:
        queryset = models.SchemaVersion.objects.all()
        resource_name = 'schema_version'
        authentication = BasicAuthentication()
        authorization = ReadOnlyAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        filtering = {
            'database_schema': ALL_WITH_RELATIONS
        }

    def prepend_urls(self):
        return [
            url(
                r'^(?P<resource_name>%s)/save_schema_dump/$' % (self._meta.resource_name,),
                self.wrap_view('save_schema_dump'),
                name='api_save_schema_dump',
            ),
        ]

    def save_schema_dump(self, request, **kwargs):
        """Creates database schema (if needed) and schema version..

        request.raw_post_data should be in the following form:
        {
            'server_id': 1,
            'database_schema_name': 'test',
        }
        """
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        schema_version = None
        data = {}
        try:
            raw_post_data = json.loads(request.raw_post_data)
            server_id = int(raw_post_data['server_id'])
            database_schema_name = raw_post_data['database_schema_name']

            schema_version = businesslogic.save_schema_dump(server_id, database_schema_name, request.user.schemanizer_user)
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(obj=schema_version, data=data, request=request)
        if schema_version and schema_version.pk:
            bundle = self.full_dehydrate(bundle)

        return self.create_response(request, bundle)


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
        authorization = ReadOnlyAuthorization()
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
                r'^(?P<resource_name>%s)/update/(?P<changeset_id>\d+)/$' % (self._meta.resource_name,),
                self.wrap_view('changeset_update'),
                name='api_changeset_update',
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
            url(
                r'^(?P<resource_name>%s)/soft_delete/(?P<changeset_id>\d+)/$' % (self._meta.resource_name,),
                self.wrap_view('changeset_soft_delete'),
                name='api_changeset_soft_delete',
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
        #self.throttle_check(request)

        changeset = None
        data = {}
        try:
            raw_post_data = json.loads(request.raw_post_data)
            allowed_fields = ('database_schema', 'type', 'classification', 'version_control_url')
            changeset_data = raw_post_data['changeset']
            for k, v in changeset_data.iteritems():
                if k not in allowed_fields:
                    raise Exception('Changeset has invalid field \'%s\'.' % (k,))
            changeset_data['database_schema'] = models.DatabaseSchema.objects.get(pk=int(changeset_data['database_schema']))
            changeset = models.Changeset(**changeset_data)

            changeset_details_data = raw_post_data['changeset_details']
            changeset_details = []
            for changeset_detail_data in changeset_details_data:
                changeset_detail = models.ChangesetDetail(**changeset_detail_data)
                changeset_details.append(changeset_detail)

            changeset = businesslogic.changeset_submit(changeset, changeset_details, request.user.schemanizer_user)
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(obj=changeset, data=data, request=request)
        if changeset and changeset.pk:
            bundle = self.full_dehydrate(bundle)

        #self.log_throttled_access(request)
        return self.create_response(request, bundle)

    def changeset_update(self, request, **kwargs):
        """Updates changeset.

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
                    'id': 1,
                    'type': 'add',
                    'description': 'create a table',
                    'apply_sql': 'create table t1...',
                    'revert_sql': 'drop table t1'
                },
                {
                    'type': 'add',
                    'description': 'create a table',
                    'apply_sql': 'create table t2...',
                    'revert_sql': 'drop table t2'
                }
            ],
            'to_be_deleted_changeset_details': [3, 4, 5]
        }
        """
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)

        changeset = None
        data = {}
        try:
            changeset_id = int(kwargs.get('changeset_id'))
            changeset = models.Changeset.objects.get(pk=changeset_id)

            post_data = json.loads(request.raw_post_data)
            changeset_data = post_data['changeset']

            allowed_fields = ('database_schema', 'type', 'classification', 'version_control_url')
            for k, v in changeset_data.iteritems():
                if k not in allowed_fields:
                    raise Exception('Changeset has invalid field \'%s\'.' % (k,))
                setattr(changeset, k, v)

            to_be_deleted_changeset_details_data = post_data['to_be_deleted_changeset_details']
            to_be_deleted_changeset_details = []
            for tbdcdd in to_be_deleted_changeset_details_data:
                tbdcd = models.ChangesetDetail.objects.get(pk=tbdcdd)
                to_be_deleted_changeset_details.append(tbdcd)

            changeset_details_data = post_data['changeset_details']
            changeset_details = []
            for cdd in changeset_details_data:
                if 'id' in cdd:
                    changeset_detail = models.ChangesetDetail.objects.get(pk=int(cdd['id']))
                else:
                    changeset_detail = models.ChangesetDetail()
                for k, v in cdd.iteritems():
                    if k not in ('id',):
                        setattr(changeset_detail, k, v)
                changeset_details.append(changeset_detail)

            changeset = businesslogic.changeset_update(changeset, changeset_details,
                to_be_deleted_changeset_details, request.user.schemanizer_user)
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(obj=changeset, data=data, request=request)
        if changeset and changeset.pk:
            bundle = self.full_dehydrate(bundle)

        return self.create_response(request, bundle)

    def changeset_reject(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)
        #self.throttle_check(request)

        changeset = None
        data = {}
        try:
            changeset = businesslogic.changeset_reject(int(kwargs['changeset_id']), request.user.schemanizer_user)
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(obj=changeset, data=data, request=request)
        if changeset and changeset.pk:
            bundle = self.full_dehydrate(bundle)

        #self.log_throttled_access(request)
        return self.create_response(request, bundle)

    def changeset_approve(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)
        #self.throttle_check(request)

        changeset = None
        data = {}
        try:
            changeset = businesslogic.changeset_approve(int(kwargs['changeset_id']), request.user.schemanizer_user)
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(obj=changeset, data=data, request=request)
        if changeset and changeset.pk:
            bundle = self.full_dehydrate(bundle)

        #self.log_throttled_access(request)
        return self.create_response(request, bundle)

    def changeset_soft_delete(self, request, **kwargs):
        self.method_check(request, allowed=['post'])
        self.is_authenticated(request)
        #self.throttle_check(request)

        changeset = None
        data = {}
        try:
            changeset = businesslogic.soft_delete_changeset(int(kwargs['changeset_id']), request.user.schemanizer_user)
        except Exception, e:
            log.exception('EXCEPTION')
            data['error_message'] = '%s' % (e,)
        bundle = self.build_bundle(obj=changeset, data=data, request=request)
        if changeset and changeset.pk:
            bundle = self.full_dehydrate(bundle)

        #self.log_throttled_access(request)
        return self.create_response(request, bundle)


class ChangesetDetailResource(ModelResource):
    changeset = fields.ForeignKey(ChangesetResource, 'changeset', null=True, blank=True, full=True)

    class Meta:
        queryset = models.ChangesetDetail.objects.all()
        resource_name = 'changeset_detail'
        authentication = BasicAuthentication()
        authorization = ReadOnlyAuthorization()
        list_allowed_methods = ['get']
        detail_allowed_methods = ['get']
        filtering = {
            'changeset': ALL_WITH_RELATIONS,
        }

