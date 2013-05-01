import logging
from pprint import pformat
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.test import TestCase, Client
from django.utils import timezone

from schemanizer import models
from schemanizer import businesslogic

log = logging.getLogger(__name__)


class HomeViewTestCase(TestCase):
    fixtures = ['schemanizer/test.yaml']

    def setUp(self):
        # usernames and passwords
        self.users = (
            ('dev', 'dev'),
            ('dba', 'dba'),
            ('admin', 'admin')
        )

    def _login(self, client, username, password):
        logged_in = client.login(username=username, password=password)
        self.assertTrue(logged_in)

    def test_home(self):
        url = reverse('home')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            self.assertTrue(r.context['user_has_access'])

            user = r.context['user']
            role_name = user.role.name

            if role_name in [models.Role.ROLE_DEVELOPER]:
                # developers should not be able to review changesets
                self.assertTrue('show_to_be_reviewed_changesets' not in r.context)
                self.assertTrue('can_apply_changesets' not in r.context)
                self.assertTrue('changesets' not in r.context)
            elif role_name in [models.Role.ROLE_DBA, models.Role.ROLE_ADMIN]:
                self.assertTrue(r.context['show_to_be_reviewed_changesets'])
                self.assertTrue(r.context['can_apply_changesets'])
                self.assertTrue('changesets' in r.context)


class UserViewsTestCase(TestCase):
    fixtures = ['schemanizer/test.yaml']

    def setUp(self):
        # usernames and passwords
        self.users = (
            ('dev', 'dev'),
            ('dba', 'dba'),
            ('admin', 'admin')
        )

    def _login(self, client, username, password):
        logged_in = client.login(username=username, password=password)
        self.assertTrue(logged_in)

    def test_user_list(self):
        url = reverse('schemanizer_users')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            # assert that expected context variables are present
            self.assertTrue('user' in r.context)
            self.assertTrue('user_has_access' in r.context)

            user = r.context['user']

            if user.role.name in [models.Role.ROLE_ADMIN]:
                # only admins can view user list
                self.assertTrue(r.context['user_has_access'])
                self.assertTrue('users' in r.context)
            else:
                # other users can't view user list
                self.assertFalse(r.context['user_has_access'])
                self.assertTrue('users' not in r.context)

    def test_user_create(self):
        url = reverse('schemanizer_user_create')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            # assert that expected context variables are present
            self.assertTrue('user' in r.context)
            self.assertTrue('user_has_access' in r.context)

            user = r.context['user']

            if user.role.name in [models.Role.ROLE_ADMIN]:
                # only admin can access view, and is presented a form
                self.assertTrue(r.context['user_has_access'])
                self.assertTrue('form' in r.context)
            else:
                self.assertFalse(r.context['user_has_access'])
                self.assertFalse('form' in r.context)

    def test_user_create_post(self):
        url = reverse('schemanizer_user_create')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)

            role = models.Role.objects.get(name=models.Role.ROLE_DEVELOPER)
            data = dict(
                name='test_dev',
                email='test_dev@example.com',
                role=role.id,
                password='test_dev',
                confirm_password='test_dev',
            )

            r = c.post(url, data)

            if u == 'admin':
                self.assertRedirects(r, reverse('schemanizer_users'))
                # user should now exist
                created_user = models.User.objects.get(name=data['name'])
                businesslogic.delete_user(created_user)
            else:
                self.assertFalse(r.context['user_has_access'])

    def _create_user_dev(self):
        role = models.Role.objects.get(name=models.Role.ROLE_DEVELOPER)
        created_user = businesslogic.create_user(
            name='test_dev',
            email='test_dev@example.com',
            role=role,
            password='test_dev')
        return created_user

    def test_user_update(self):
        created_user = self._create_user_dev()
        created_user_id = created_user.id

        try:
            url = reverse('schemanizer_update_user', args=[created_user_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                r = c.get(url)

                # required context vars should be present
                self.assertTrue('user' in r.context)
                self.assertTrue('user_has_access' in r.context)

                user = r.context['user']

                if user.role.name in [models.Role.ROLE_ADMIN]:
                    # only admins should have access and are presented with form
                    self.assertTrue(r.context['user_has_access'])
                    self.assertTrue('form' in r.context)
                else:
                    self.assertFalse(r.context['user_has_access'])
                    self.assertFalse('form' in r.context)
        finally:
            businesslogic.delete_user(created_user_id)

    def test_user_update_post(self):
        created_user = self._create_user_dev()
        created_user_id = created_user.id

        try:
            url = reverse('schemanizer_update_user', args=[created_user_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)

                new_role = models.Role.objects.get(name=models.Role.ROLE_DBA)
                data = dict(
                    name='test_dev_updated',
                    email='test_dev_updated@example.com',
                    role=new_role.id,)
                r = c.post(url, data=data)

                if u == 'admin':
                    # only admins can update users
                    self.assertRedirects(r, reverse('schemanizer_users'))

                    # check that updates did went through
                    updated_user = models.User.objects.get(pk=created_user_id)
                    self.assertEqual(updated_user.name, data['name'])
                    self.assertEqual(updated_user.email, data['email'])
                    self.assertEqual(updated_user.role_id, data['role'])
                else:
                    self.assertFalse(r.context['user_has_access'])
        finally:
            businesslogic.delete_user(created_user_id)

    def test_user_delete(self):
        created_user = self._create_user_dev()
        created_user_id = created_user.id

        try:
            url = reverse(
                'schemanizer_confirm_delete_user',
                args=[created_user_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                r = c.get(url)

                user = r.context['user']

                if user.role.name in [models.Role.ROLE_ADMIN]:
                    self.assertTrue(r.context['user_has_access'])
                    self.assertTrue('to_be_del_user' in r.context)
                else:
                    self.assertFalse(r.context['user_has_access'])
        finally:
            businesslogic.delete_user(created_user_id)

    def test_user_delete_post(self):
        created_user = self._create_user_dev()
        create_user_id = created_user.id

        try:
            url = reverse(
                'schemanizer_confirm_delete_user', args=[create_user_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                data = dict(confirm_delete='Confirm')
                r = c.post(url, data=data)

                if u == 'admin':
                    self.assertRedirects(r, reverse('schemanizer_users'))
                    qs = models.User.objects.filter(pk=create_user_id)
                    self.assertFalse(qs.exists())
                else:
                    self.assertFalse(r.context['user_has_access'])

        finally:
            models.User.objects.filter(pk=create_user_id).delete()


class ChangesetViewsTestCase(TestCase):
    fixtures = ['schemanizer/test.yaml']

    def setUp(self):
        # usernames and passwords
        self.users = (
            ('dev', 'dev'),
            ('dba', 'dba'),
            ('admin', 'admin')
        )

        self.database_schema = models.DatabaseSchema.objects.create(
            name='test_schemanizer_schema_1'
        )
        log.debug('Database schema [id=%s] was created.' % (
            self.database_schema.id,))

    def tearDown(self):
        database_schema_id = self.database_schema.id
        self.database_schema.delete()
        log.debug('Database schema [id=%s] was deleted.' % (
            database_schema_id,))

    def _login(self, client, username, password):
        logged_in = client.login(username=username, password=password)
        self.assertTrue(logged_in)

    def _create_changeset(self):
        user = models.User.objects.get(name='dev')
        with transaction.commit_on_success():
            changeset = models.Changeset.objects.create(
                database_schema=self.database_schema,
                type=models.Changeset.DDL_TABLE_CREATE,
                classification=models.Changeset.CLASSIFICATION_PAINLESS,
                review_status=models.Changeset.REVIEW_STATUS_NEEDS,
                submitted_by=user,
                submitted_at=timezone.now())
            models.ChangesetDetail.objects.create(
                changeset=changeset,
                type=models.ChangesetDetail.TYPE_ADD,
                description='create table_1',
                apply_sql="""
                    create table `table_1` (
                        `id` int primary key auto_increment,
                        `name` varchar(255)
                    )
                    """,
                revert_sql="""
                    drop table `table_1`
                    """)
        log.info('Changeset [id=%s] was created.' % (changeset.id,))
        return changeset

    def test_changeset_list(self):
        url = reverse('schemanizer_changeset_list')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            self.assertTrue('user' in r.context)
            self.assertTrue('user_has_access' in r.context)

            # everyone can view changeset list
            self.assertTrue(r.context['user_has_access'])
            self.assertTrue('changesets' in r.context)

            user = r.context['user']

            if user.role.name in [models.Role.ROLE_ADMIN]:
                # only admins can soft delete changeset
                self.assertTrue(r.context['can_soft_delete'])
            else:
                self.assertFalse(r.context['can_soft_delete'])

    def test_changeset_submit(self):
        url = reverse('schemanizer_changeset_submit')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            user_has_access = r.context['user_has_access']
            self.assertTrue(user_has_access)

    def test_changeset_submit_post(self):
        url = reverse('schemanizer_changeset_submit')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            data = {}
            # changeset data
            changeset_data = dict(
                database_schema=self.database_schema.id,
                type=models.Changeset.DDL_TABLE_CREATE,
                classification=models.Changeset.CLASSIFICATION_PAINLESS,
                version_control_url='123456'
            )
            data.update(changeset_data)
            # form management data
            data.update({
                'changeset_details-TOTAL_FORMS': '2',
                'changeset_details-INITIAL_FORMS': '0',
                'changeset_details-MAX_NUM_FORMS': '1000'})
            # changeset details data
            changeset_details_data = {
                'changeset_details-0-type': models.ChangesetDetail.TYPE_ADD,
                'changeset_details-0-description': 'Add table `table2`',
                'changeset_details-0-apply_sql': """
                    create table `table2` (
                        `id` int primary key auto_increment,
                        `name` varchar(255)
                    )
                    """,
                'changeset_details-0-revert_sql': """
                    drop table `table2`;
                    """,
                'changeset_details-1-type': models.ChangesetDetail.TYPE_ADD,
                'changeset_details-1-description': 'Add table `table2`',
                'changeset_details-1-apply_sql': """
                    create table `table2` (
                        `id` int primary key auto_increment,
                        `name` varchar(255)
                    )
                    """,
                'changeset_details-1-revert_sql': """
                    drop table `table2`;
                    """,
                }
            data.update(changeset_details_data)
            r = c.post(url, data=data)

            changeset = None
            try:
                changesets = models.Changeset.objects.filter(
                    version_control_url='123456')
                self.assertTrue(changesets.exists())
                if changesets.exists():
                    changeset = changesets[0]
                    self.assertEqual(changeset.changeset_details.all().count(), 2)
            finally:
                if changeset:
                    businesslogic.delete_changeset(changeset)

    def test_changeset_view(self):
        changeset = self._create_changeset()
        changeset_id = changeset.id

        try:
            url = reverse('schemanizer_changeset_view', args=[changeset_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                r = c.get(url)

                self.assertTrue(r.context['user_has_access'])
                self.assertTrue('can_update' in r.context)
                self.assertTrue('can_set_review_status_to_in_progress' in r.context)
                self.assertTrue('can_approve' in r.context)
                self.assertTrue('can_reject' in r.context)
                self.assertTrue('can_soft_delete' in r.context)
        finally:
            businesslogic.delete_changeset(changeset_id)

    def test_changeset_view_post(self):
        """Test changeset posts."""

        changeset = self._create_changeset()
        changeset_id = changeset.id

        try:
            url = reverse('schemanizer_changeset_view', args=[changeset_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                user = models.User.objects.get(name=u)
                can_update = businesslogic.changeset_can_be_updated_by_user(
                    changeset, user)
                can_set_review_status_to_in_progress = businesslogic.changeset_can_be_reviewed_by_user(
                    changeset, user)
                can_approve = businesslogic.changeset_can_be_approved_by_user(
                    changeset, user)
                can_reject = businesslogic.changeset_can_be_rejected_by_user(
                    changeset, user)
                can_soft_delete = businesslogic.changeset_can_be_soft_deleted_by_user(
                    changeset, user)
                if can_update:
                    r = c.post(url, data=dict(submit_update=u'Submit'))
                    self.assertRedirects(
                        r, reverse(
                            'schemanizer_changeset_update', args=[changeset_id]))
                if can_set_review_status_to_in_progress:
                    changeset = models.Changeset.objects.get(pk=changeset_id)
                    changeset.review_status = models.Changeset.REVIEW_STATUS_NEEDS
                    changeset.save()
                    r = c.post(url, data=dict(submit_review=u'Submit'))
                    self.assertRedirects(
                        r, reverse(
                            'schemanizer_changeset_review', args=[changeset_id]))
                if can_approve:
                    changeset = models.Changeset.objects.get(pk=changeset_id)
                    changeset.review_status = models.Changeset.REVIEW_STATUS_NEEDS
                    changeset.save()
                    r = c.post(url, data=dict(submit_approve=u'Submit'))
                    tmp_changeset = models.Changeset.objects.get(pk=changeset_id)
                    self.assertEqual(
                        tmp_changeset.review_status,
                        models.Changeset.REVIEW_STATUS_APPROVED)
                if can_reject:
                    changeset = models.Changeset.objects.get(pk=changeset_id)
                    changeset.review_status = models.Changeset.REVIEW_STATUS_NEEDS
                    changeset.save()
                    r = c.post(url, data=dict(submit_reject=u'Submit'))
                    tmp_changeset = models.Changeset.objects.get(pk=changeset_id)
                    self.assertEqual(
                        tmp_changeset.review_status,
                        models.Changeset.REVIEW_STATUS_REJECTED)
                if can_soft_delete:
                    r = c.post(url, data=dict(submit_delete=u'Submit'))
                    self.assertRedirects(
                        r, reverse(
                            'schemanizer_changeset_soft_delete',
                            args=[changeset_id]))

        finally:
            businesslogic.delete_changeset(changeset_id)

    def test_changeset_update(self):
        c = Client()
        for u, p in self.users:
            self._login(c, u, p)
            user = models.User.objects.get(name=u)
            changeset = self._create_changeset()
            changeset_id = changeset.id
            try:
                url = reverse('schemanizer_changeset_update', args=[changeset_id])
                r = c.get(url)

                self.assertTrue(r.context['user_has_access'])
                if businesslogic.changeset_can_be_updated_by_user(changeset, user):
                    self.assertTrue('changeset_form' in r.context)
                    self.assertTrue('changeset_detail_formset' in r.context)
            finally:
                businesslogic.delete_changeset(changeset_id)

    def test_changeset_update_post(self):
        c = Client()
        for u, p in self.users:
            self._login(c, u, p)
            user = models.User.objects.get(name=u)
            changeset = self._create_changeset()
            changeset_id = changeset.id
            try:
                changeset_detail = changeset.changeset_details.all()[0]
                url = reverse('schemanizer_changeset_update', args=[changeset_id])
                if businesslogic.changeset_can_be_updated_by_user(changeset, user):
                    data = {}
                    # changeset data
                    data.update(dict(
                        database_schema=changeset.database_schema_id,
                        type=changeset.type,
                        classification=changeset.classification,
                        version_control_url=changeset.version_control_url,
                    ))
                    # form management data
                    data.update({
                        'changeset_details-TOTAL_FORMS': 2,
                        'changeset_details-INITIAL_FORMS': 1,
                        'changeset_details-MAX_NUM_FORMS': 1000
                    })
                    # changeset details data
                    data.update({
                        'changeset_details-0-changeset': changeset_id,
                        'changeset_details-0-type': changeset_detail.type,
                        'changeset_details-0-description': changeset_detail.description,
                        'changeset_details-0-apply_sql': changeset_detail.apply_sql,
                        'changeset_details-0-revert_sql': changeset_detail.revert_sql,
                        'changeset_details-0-before_checksum': changeset_detail.before_checksum,
                        'changeset_details-0-after_checksum': changeset_detail.after_checksum,
                        'changeset_details-0-count_sql': changeset_detail.count_sql,
                        'changeset_details-0-volumetric_values': changeset_detail.volumetric_values,
                        'changeset_details-0-id': changeset_detail.id,
                        'changeset_details-1-changeset': changeset_id,
                        'changeset_details-1-type': models.ChangesetDetail.TYPE_ADD,
                        })
                    r = c.post(url, data=data)
                    tmp_changeset = models.Changeset.objects.get(pk=changeset_id)
                    self.assertEqual(
                        tmp_changeset.review_status,
                        models.Changeset.REVIEW_STATUS_NEEDS)

            finally:
                businesslogic.delete_changeset(changeset_id)

    def test_confirm_soft_delete_changeset(self):
        c = Client()
        for u, p in self.users:
            self._login(c, u, p)

            user = models.User.objects.get(name=u)
            changeset = self._create_changeset()
            changeset_id = changeset.id
            try:
                url = reverse(
                    'schemanizer_changeset_soft_delete',
                    args=[changeset_id])
                r = c.get(url)
                self.assertTrue('user_has_access' in r.context)
            finally:
                businesslogic.delete_changeset(changeset)

    def test_confirm_soft_delete_changeset_post(self):
        c = Client()
        for u, p in self.users:
            self._login(c, u, p)

            user = models.User.objects.get(name=u)
            changeset = self._create_changeset()
            changeset_id = changeset.id
            try:
                url = reverse(
                    'schemanizer_changeset_soft_delete',
                    args=[changeset_id])
                if businesslogic.changeset_can_be_soft_deleted_by_user(
                        changeset, user):
                    r = c.post(url, data=dict(confirm_soft_delete='Submit'))
                    tmp_changeset = models.Changeset.objects.get(pk=changeset_id)
                    self.assertTrue(tmp_changeset.is_deleted)
            finally:
                businesslogic.delete_changeset(changeset)

    def test_changeset_review(self):
        c = Client()
        for u, p in self.users:
            self._login(c, u, p)

            user = models.User.objects.get(name=u)
            changeset = None
            schema_version = None

            try:
                changeset = self._create_changeset()
                changeset_id = changeset.id

                ddl = ''
                schema_version = models.SchemaVersion.objects.create(
                    database_schema=self.database_schema,
                    ddl=ddl,
                    checksum='123456'
                )
                schema_version_id = schema_version.id

                user_has_access = businesslogic.changeset_can_be_reviewed_by_user(changeset, user)
                url = reverse('schemanizer_changeset_review', args=[changeset_id])
                r = c.get(url)
                if u in ('dba', 'admin'):
                    self.assertTrue(user_has_access)
                else:
                    self.assertFalse(user_has_access)
                if user_has_access:
                    self.assertTrue('select_schema_version_form' in r.context)

                r = c.get(url, data=dict(schema_version=schema_version_id))
                if user_has_access:
                    self.assertTrue('thread' in r.context)
                    self.assertTrue(r.context['thread_started'])
                    thread = r.context['thread']
                    # wait for thread to end
                    log.debug('Waiting for review thread to end...')
                    thread.join()
                    log.debug('Review thread ended.')

            finally:
                if schema_version:
                    schema_version.delete()
                if changeset:
                    businesslogic.delete_changeset(changeset)



class ServerViewsTestCase(TestCase):
    fixtures = ['schemanizer/test.yaml']

    def setUp(self):
        # usernames and passwords
        self.users = (
            ('dev', 'dev'),
            ('dba', 'dba'),
            ('admin', 'admin')
        )

    def _login(self, client, username, password):
        logged_in = client.login(username=username, password=password)
        self.assertTrue(logged_in)

    def test_server_list(self):
        url = reverse('schemanizer_server_list')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            # assert that expected context variables are present
            self.assertTrue('user' in r.context)
            self.assertTrue('user_has_access' in r.context)

            user = r.context['user']

            self.assertTrue(r.context['user_has_access'])
            self.assertTrue('servers' in r.context)

    def test_server_create(self):
        url = reverse('schemanizer_server_create')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            # assert that expected context variables are present
            self.assertTrue('user' in r.context)
            self.assertTrue('user_has_access' in r.context)

            user = r.context['user']

            # everyone can create entry for servers
            self.assertTrue(r.context['user_has_access'])
            self.assertTrue('form' in r.context)

    def test_server_create_post(self):
        url = reverse('schemanizer_server_create')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)

            environment = models.Environment.objects.get(name='test')
            data = dict(
                name='test_localhost',
                hostname='localhost',
                environment=environment.id
            )
            r = c.post(url, data)

            server = models.Server.objects.filter(name=data['name'])
            try:
                self.assertTrue(server.exists())
                self.assertRedirects(r, reverse('schemanizer_server_list'))
            finally:
                models.Server.objects.filter(name=data['name']).delete()

    def _create_server(self):
        environment = models.Environment.objects.get(name='test')
        server = models.Server.objects.create(
            name='test_localhost',
            hostname='localhost',
            environment=environment
        )
        return server

    def test_server_update(self):
        for u, p in self.users:
            server = self._create_server()
            server_id = server.id

            try:
                url = reverse('schemanizer_server_update', args=[server_id])
                c = Client()
                self._login(c, u, p)
                r = c.get(url)

                self.assertTrue('user' in r.context)
                self.assertTrue('user_has_access' in r.context)
                self.assertTrue('form' in r.context)

            finally:
                models.Server.objects.filter(pk=server_id).delete()

    def test_server_update_post(self):
        for u, p in self.users:
            server = self._create_server()
            server_id = server.id
            try:
                url = reverse('schemanizer_server_update', args=[server_id])
                c = Client()

                self._login(c, u, p)

                environment = models.Environment.objects.get(name='test')
                data = dict(
                    name='test_localhost_new',
                    hostname='localhost_new',
                    environment=environment.id
                )
                r = c.post(url, data)

                self.assertTrue(models.Server.objects.filter(pk=server_id).exists())
                self.assertRedirects(r, reverse('schemanizer_server_list'))
            finally:
                models.Server.objects.filter(pk=server_id).delete()

    def test_server_delete(self):
        for u, p in self.users:
            server = self._create_server()
            server_id = server.id

            try:
                url = reverse('schemanizer_server_delete', args=[server_id])
                c = Client()
                self._login(c, u, p)
                r = c.get(url)

                self.assertTrue('user' in r.context)
                self.assertTrue('user_has_access' in r.context)
                self.assertTrue('form' in r.context)

            finally:
                models.Server.objects.filter(pk=server_id).delete()

    def test_server_delete_post(self):
        for u, p in self.users:
            server = self._create_server()
            server_id = server.id

            url = reverse('schemanizer_server_delete', args=[server_id])
            c = Client()
            self._login(c, u, p)
            r = c.post(url)

            self.assertFalse(models.Server.objects.filter(pk=server_id).exists())
            self.assertRedirects(r, reverse('schemanizer_server_list'))


class EnvironmentViewsTestCase(TestCase):
    fixtures = ['schemanizer/test.yaml']

    def setUp(self):
        # usernames and passwords
        self.users = (
            ('dev', 'dev'),
            ('dba', 'dba'),
            ('admin', 'admin')
        )

    def _login(self, client, username, password):
        logged_in = client.login(username=username, password=password)
        self.assertTrue(logged_in)

    def test_environment_list(self):
        url = reverse('schemanizer_environment_list')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            # assert that expected context variables are present
            self.assertTrue('user' in r.context)
            self.assertTrue('user_has_access' in r.context)
            self.assertTrue('qs' in r.context)
            self.assertTrue('can_add' in r.context)
            self.assertTrue('can_update' in r.context)
            self.assertTrue('can_delete' in r.context)

            user = r.context['user']

    def test_environment_create(self):
        url = reverse('schemanizer_environment_create')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            # assert that expected context variables are present
            self.assertTrue('user' in r.context)
            self.assertTrue('user_has_access' in r.context)

            user = r.context['user']

            if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
                self.assertTrue(r.context['user_has_access'])
                self.assertTrue('form' in r.context)
            else:
                self.assertFalse(r.context['user_has_access'])

    def test_environment_create_post(self):
        url = reverse('schemanizer_environment_create')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)

            data = dict(
                name='test_env'
            )
            r = c.post(url, data)

            qs = None
            try:
                if u in ('dba', 'admin'):
                    qs = models.Environment.objects.filter(name=data['name'])
                    self.assertTrue(qs.exists())
                    self.assertRedirects(r, reverse('schemanizer_environment_list'))
                else:
                    self.assertFalse(r.context['user_has_access'])
            finally:
                models.Environment.objects.filter(name=data['name']).delete()


    def _create_environment(self):
        o = models.Environment.objects.create(
            name='test_env'
        )
        return o

    def test_environment_update(self):
        for u, p in self.users:
            env = self._create_environment()
            env_id = env.id

            try:
                url = reverse('schemanizer_environment_update', args=[env_id])
                c = Client()
                self._login(c, u, p)
                r = c.get(url)

                self.assertTrue('user' in r.context)
                self.assertTrue('user_has_access' in r.context)

                user = r.context['user']
                if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
                    self.assertTrue(r.context['user_has_access'])
                    self.assertTrue('form' in r.context)
                else:
                    self.assertFalse(r.context['user_has_access'])

            finally:
                models.Server.objects.filter(pk=env_id).delete()


    def test_environment_update_post(self):
        for u, p in self.users:
            env = self._create_environment()
            env_id = env.id
            try:
                url = reverse('schemanizer_environment_update', args=[env_id])
                c = Client()

                self._login(c, u, p)

                data = dict(
                    name='test_env_new'
                )
                r = c.post(url, data)

                if u in ('dba', 'admin'):
                    self.assertTrue(models.Environment.objects.filter(pk=env_id).exists())
                    self.assertRedirects(r, reverse('schemanizer_environment_list'))
                else:
                    self.assertFalse(r.context['user_has_access'])
            finally:
                models.Environment.objects.filter(pk=env_id).delete()

    def test_environment_del(self):
        for u, p in self.users:
            env = self._create_environment()
            env_id = env.id

            try:
                url = reverse('schemanizer_environment_del', args=[env_id])
                c = Client()
                self._login(c, u, p)
                r = c.get(url)

                self.assertTrue('user' in r.context)
                user = r.context['user']
                self.assertTrue('user_has_access' in r.context)

                if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
                    self.assertTrue(r.context['user_has_access'])
                else:
                    self.assertFalse(r.context['user_has_access'])

            finally:
                models.Environment.objects.filter(pk=env_id).delete()

    def test_environment_del_post(self):
        for u, p in self.users:
            env = self._create_environment()
            env_id = env.id

            url = reverse('schemanizer_environment_del', args=[env_id])
            c = Client()
            self._login(c, u, p)
            r = c.post(url)

            if u in ('dba', 'admin'):
                self.assertFalse(models.Environment.objects.filter(pk=env_id).exists())
            else:
                self.assertFalse(r.context['user_has_access'])


class DatabaseSchemaViewsTestCase(TestCase):
    fixtures = ['schemanizer/test.yaml']

    def setUp(self):
        # usernames and passwords
        self.users = (
            ('dev', 'dev'),
            ('dba', 'dba'),
            ('admin', 'admin')
        )

    def _login(self, client, username, password):
        logged_in = client.login(username=username, password=password)
        self.assertTrue(logged_in)

    def test_database_schema_list(self):
        url = reverse('schemanizer_database_schema_list')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            # everyone has access to database schema list
            self.assertTrue(r.context['user_has_access'])
            self.assertTrue('database_schemas' in r.context)

class SchemaVersionViewsTestCase(TestCase):
    fixtures = ['schemanizer/test.yaml']

    def setUp(self):
        # usernames and passwords
        self.users = (
            ('dev', 'dev'),
            ('dba', 'dba'),
            ('admin', 'admin')
        )

    def _login(self, client, username, password):
        logged_in = client.login(username=username, password=password)
        self.assertTrue(logged_in)

    def test_schema_version_list(self):
        database_schema = models.DatabaseSchema.objects.create(
            name='test_schemanizer_schema_1'
        )
        try:
            url = reverse('schemanizer_schema_version_list')
            url = '%s?%s' % (url, urllib.urlencode(dict(
                database_schema=database_schema.id)))
            c = Client()
            for u, p in self.users:
                self._login(c, u, p)
                r = c.get(url)

                self.assertTrue(r.context['user_has_access'])
                self.assertTrue('schema_versions' in r.context)
        finally:
            database_schema.delete()

    def test_schema_version_create(self):
        environment = models.Environment.objects.get(name='test')
        server = models.Server.objects.create(
            name='test_server_1',
            hostname='localhost',
            environment=environment
        )
        server_id = server.id
        try:
            url = reverse('schemanizer_schema_version_create', args=[server_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                r = c.get(url)

                self.assertTrue(r.context['user_has_access'])
                self.assertTrue('form' in r.context)
        finally:
            server.delete()

    def test_schema_version_create_post(self):
        environment = models.Environment.objects.get(name='test')
        server = models.Server.objects.create(
            name='test_server_1',
            hostname='localhost',
            environment=environment
        )
        server_id = server.id
        try:
            url = reverse('schemanizer_schema_version_create', args=[server_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                data = dict(schema='information_schema')
                r = c.post(url, data)

                self.assertRedirects(r, reverse('schemanizer_server_list'))
        finally:
            server.delete()

    def test_schema_version_view(self):
        database_schema = None
        schema_version = None
        try:
            database_schema = models.DatabaseSchema.objects.create(
                name='test_schemanizer_schema_1'
            )
            schema_version = models.SchemaVersion.objects.create(
                database_schema=database_schema,
                ddl='',
                checksum=''
            )
            url = reverse('schemanizer_schema_version_view', args=[schema_version.id])
            c = Client()
            for u, p in self.users:
                self._login(c, u, p)
                r = c.get(url)

                self.assertTrue(r.context['user_has_access'])
        finally:
            if database_schema:
                database_schema.delete()
            if schema_version:
                schema_version.delete()