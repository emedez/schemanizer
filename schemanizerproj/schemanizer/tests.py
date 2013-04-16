import logging
from pprint import pformat
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.test import TestCase, Client
from django.utils import timezone

from schemanizer import businesslogic
from schemanizer import models

log = logging.getLogger(__name__)


class PageAccessTestCase(TestCase):

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

    def _create_changeset(self):
        """Creates a changeset object."""
        database_schema = models.DatabaseSchema.objects.get(name=u'schemanizer1')
        user = models.User.objects.get(name=u'dev')
        with transaction.commit_on_success():
            changeset = models.Changeset.objects.create(
                database_schema=database_schema,
                type=models.Changeset.DDL_TABLE_CREATE,
                classification=models.Changeset.CLASSIFICATION_PAINLESS,
                version_control_url=u'https://',
                review_status=models.Changeset.REVIEW_STATUS_NEEDS,
                submitted_by=user,
                submitted_at=timezone.now())
            models.ChangesetDetail.objects.create(
                changeset=changeset,
                type=models.ChangesetDetail.TYPE_ADD,
                description=u'create table `tables1`',
                apply_sql=u"""
                    create table `tables1` (
                        `id` int primary key auto_increment,
                        `name` varchar(255)
                    );
                    """,
                revert_sql=u"""
                    drop table `tables1`;
                    """)
        log.info('Changeset [id=%s] was created.' % (changeset.id,))
        return changeset

    def test_home(self):
        """Tests home page access."""

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

    def test_user_list(self):
        """Tests user list page access."""

        url = reverse('schemanizer_users')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            user = r.context['user']
            role_name = user.role.name

            if role_name in [models.Role.ROLE_ADMIN]:
                self.assertTrue(r.context['user_has_access'])
                self.assertTrue('users' in r.context)
            else:
                self.assertFalse(r.context['user_has_access'])
                self.assertTrue('users' not in r.context)

    def test_user_create(self):
        """Tests user create page access."""

        url = reverse('schemanizer_user_create')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            user = r.context['user']
            role_name = user.role.name

            if role_name in [models.Role.ROLE_ADMIN]:
                self.assertTrue(r.context['user_has_access'])
                self.assertTrue('form' in r.context)
            else:
                self.assertFalse(r.context['user_has_access'])

    def test_user_create_post(self):
        """Tests user create post."""

        url = reverse('schemanizer_user_create')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            role = models.Role.objects.get(name=models.Role.ROLE_DEVELOPER)
            data = dict(
                name='test_dev',
                email='EMedez+test_dev@palominodb.com',
                role=role.id,
                password='test_dev',
                confirm_password='test_dev',
            )
            r = c.post(url, data)

            if u == 'admin':
                self.assertRedirects(r, reverse('schemanizer_users'))
                created_user = models.User.objects.get(name=data['name'])
                businesslogic.delete_user(created_user)
            else:
                self.assertFalse(r.context['user_has_access'])

    def test_user_update(self):
        """Tests user update page access."""

        role = models.Role.objects.get(name=models.Role.ROLE_DEVELOPER)
        created_user = businesslogic.create_user(
            name='test_dev',
            email='EMedez+test_dev@palominodb.com',
            role=role,
            password='test_dev')
        created_user_id = created_user.id

        try:
            url = reverse('schemanizer_update_user', args=[created_user_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                r = c.get(url)

                user = r.context['user']
                role_name = user.role.name

                if role_name in [models.Role.ROLE_ADMIN]:
                    self.assertTrue(r.context['user_has_access'])
                    self.assertTrue('form' in r.context)
                else:
                    self.assertFalse(r.context['user_has_access'])
        finally:
            businesslogic.delete_user(created_user_id)

    def test_user_update_post(self):
        """Tests user update posts."""

        role = models.Role.objects.get(name=models.Role.ROLE_DEVELOPER)
        created_user = businesslogic.create_user(
            name='test_dev',
            email='EMedez+test_dev@palominodb.com',
            role=role,
            password='test_dev')
        created_user_id = created_user.id

        try:
            url = reverse('schemanizer_update_user', args=[created_user_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                new_role = models.Role.objects.get(name=models.Role.ROLE_DBA)
                data = dict(
                    name='test_dev_updated',
                    email='EMedez+test_dev_updated@palominodb.com',
                    role=new_role.id,)
                r = c.post(url, data=data)

                if u == 'admin':
                    self.assertRedirects(r, reverse('schemanizer_users'))

                    updated_user = models.User.objects.get(pk=created_user_id)
                    self.assertEqual(updated_user.name, 'test_dev_updated')
                    self.assertEqual(updated_user.email, 'EMedez+test_dev_updated@palominodb.com')
                    self.assertEqual(updated_user.role_id, new_role.id)
                else:
                    self.assertFalse(r.context['user_has_access'])
        finally:
            businesslogic.delete_user(created_user_id)

    def test_user_delete(self):
        """Tests user delete page access."""

        # create test user
        role = models.Role.objects.get(name=models.Role.ROLE_DEVELOPER)
        test_user = businesslogic.create_user(
            name='test',
            email='EMedez+test@palominodb.com',
            role=role,
            password='test')
        test_user_id = test_user.id

        try:
            url = reverse('schemanizer_confirm_delete_user', args=[test_user_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                r = c.get(url)

                user = r.context['user']
                role_name = user.role.name

                if role_name in [models.Role.ROLE_ADMIN]:
                    self.assertTrue(r.context['user_has_access'])
                    self.assertTrue('to_be_del_user' in r.context)
                else:
                    self.assertFalse(r.context['user_has_access'])
        finally:
            businesslogic.delete_user(test_user_id)

    def test_user_delete_post(self):
        """Tests user delete posts."""

        # create test user
        role = models.Role.objects.get(name=models.Role.ROLE_DEVELOPER)
        test_user = businesslogic.create_user(
            name='test_del',
            email='EMedez+test_del@palominodb.com',
            role=role,
            password='test_del')
        test_user_id = test_user.id

        try:
            url = reverse('schemanizer_confirm_delete_user', args=[test_user_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                data = dict(confirm_delete='Confirm')
                r = c.post(url, data=data)

                if u == 'admin':
                    self.assertRedirects(r, reverse('schemanizer_users'))
                    qs = models.User.objects.filter(pk=test_user_id)
                    self.assertFalse(qs.exists())
                else:
                    self.assertFalse(r.context['user_has_access'])

        finally:
            qs = models.User.objects.filter(pk=test_user_id)
            if qs.exists():
                businesslogic.delete_user(test_user_id)

    def test_changeset_list(self):
        """Tests changeset list page access."""

        url = reverse('schemanizer_changeset_list')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            self.assertTrue(r.context['user_has_access'])
            self.assertTrue('changesets' in r.context)

            user = r.context['user']
            role_name = user.role.name

            if role_name in [models.Role.ROLE_ADMIN]:
                self.assertTrue(r.context['can_soft_delete'])
            else:
                self.assertFalse(r.context['can_soft_delete'])

    def test_changeset_view(self):
        """Tests changeset page access."""

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
                self.assertTrue('can_review' in r.context)
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
                can_update = changeset.can_be_updated_by(user)
                can_review = changeset.can_be_reviewed_by(user)
                can_approve = changeset.can_be_approved_by(user)
                can_reject = changeset.can_be_rejected_by(user)
                can_soft_delete = changeset.can_be_soft_deleted_by(user)
                if can_update:
                    r = c.post(url, data=dict(submit_update=u'Submit'))
                    self.assertRedirects(
                        r, reverse(
                            'schemanizer_update_changeset', args=[changeset_id]))
                if can_review:
                    r = c.post(url, data=dict(submit_review=u'Submit'))
                    self.assertRedirects(
                        r, reverse(
                            'schemanizer_changeset_review', args=[changeset_id]))
                if can_approve:
                    r = c.post(url, data=dict(submit_approve=u'Submit'))
                    tmp_changeset = models.Changeset.objects.get(pk=changeset_id)
                    self.assertEqual(
                        tmp_changeset.review_status,
                        models.Changeset.REVIEW_STATUS_APPROVED)
                if can_reject:
                    r = c.post(url, data=dict(submit_reject=u'Submit'))
                    tmp_changeset = models.Changeset.objects.get(pk=changeset_id)
                    self.assertEqual(
                        tmp_changeset.review_status,
                        models.Changeset.REVIEW_STATUS_REJECTED)
                if can_soft_delete:
                    r = c.post(url, data=dict(submit_delete=u'Submit'))
                    self.assertRedirects(
                        r, reverse(
                            'schemanizer_confirm_soft_delete_changeset',
                            args=[changeset_id]))

        finally:
            businesslogic.delete_changeset(changeset_id)

    def test_changeset_submit(self):
        """Tests changeset submit page."""

        url = reverse('schemanizer_changeset_submit')
        c = Client()

        for u, p in self.users:
            self._login(c, u, p)
            r = c.get(url)

            user_has_access = r.context['user_has_access']
            self.assertTrue(user_has_access)

    def test_changeset_submit_post(self):
        """Tests changeset submit posts."""

        url = reverse('schemanizer_changeset_submit')
        c = Client()

        database_schema = models.DatabaseSchema.objects.get(name=u'schemanizer1')

        for u, p in self.users:
            self._login(c, u, p)
            data = {}
            # changeset data
            changeset_data = dict(
                database_schema=database_schema.id,
                type=models.Changeset.DDL_TABLE_CREATE,
                classification=models.Changeset.CLASSIFICATION_PAINLESS,
                version_control_url=u'123456'
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
                'changeset_details-0-description': u'Add table `table2`',
                'changeset_details-0-apply_sql': u"""
                    create table `table2` (
                        `id` int primary key auto_increment,
                        `name` varchar(255)
                    )
                    """,
                'changeset_details-0-revert_sql': u"""
                    drop table `table2`;
                    """,
                'changeset_details-1-type': models.ChangesetDetail.TYPE_ADD,
                'changeset_details-1-description': u'Add table `table2`',
                'changeset_details-1-apply_sql': u"""
                    create table `table2` (
                        `id` int primary key auto_increment,
                        `name` varchar(255)
                    )
                    """,
                'changeset_details-1-revert_sql': u"""
                    drop table `table2`;
                    """,
            }
            data.update(changeset_details_data)
            r = c.post(url, data=data)

            changeset = None
            try:
                changesets = models.Changeset.objects.filter(
                    version_control_url=u'123456')
                self.assertTrue(changesets.exists())
                if changesets.exists():
                    changeset = changesets[0]
                    self.assertEqual(changeset.changeset_details.all().count(), 2)
            finally:
                if changeset:
                    businesslogic.delete_changeset(changeset)

    def test_changeset_review(self):
        """Tests changeset review page."""

        changeset = self._create_changeset()
        changeset_id = changeset.id
        try:
            url = reverse('schemanizer_changeset_review', args=[changeset_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
                r = c.get(url)

                #
                # only dbas and admins can review changesets
                #
                if u in (u'dba', u'admin'):
                    self.assertTrue(r.context['user_has_access'])
                    self.assertTrue('changeset_form' in r.context)
                    self.assertTrue('changeset_detail_formset' in r.context)
                else:
                    self.assertFalse(r.context['user_has_access'])
        finally:
            businesslogic.delete_changeset(changeset_id)

    def test_changeset_review_post(self):
        """Tests changeset review posts."""

        changeset = self._create_changeset()
        changeset_id = changeset.id

        try:
            changeset_detail = changeset.changeset_details.all()[0]

            url = reverse('schemanizer_changeset_review', args=[changeset_id])
            c = Client()

            for u, p in self.users:
                self._login(c, u, p)
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
                #
                # only dbas and admins can review changesets
                #
                if u in (u'dba', u'admin'):
                    tmp_changeset = models.Changeset.objects.get(pk=changeset_id)
                    self.assertEqual(
                        tmp_changeset.review_status,
                        models.Changeset.REVIEW_STATUS_IN_PROGRESS)
                else:
                    self.assertFalse(r.context['user_has_access'])
        finally:
            businesslogic.delete_changeset(changeset_id)

    def test_confirm_soft_delete_changeset(self):
        """Tests confirm soft delete page."""

        c = Client()
        for u, p in self.users:
            self._login(c, u, p)

            user = models.User.objects.get(name=u)
            changeset = self._create_changeset()
            changeset_id = changeset.id
            try:
                url = reverse(
                    'schemanizer_confirm_soft_delete_changeset',
                    args=[changeset_id])
                r = c.get(url)
                self.assertTrue('user_has_access' in r.context)
            finally:
                businesslogic.delete_changeset(changeset)

    def test_confirm_soft_delete_changeset_post(self):
        """Tests confirm soft delete page posts."""

        c = Client()
        for u, p in self.users:
            self._login(c, u, p)

            user = models.User.objects.get(name=u)
            changeset = self._create_changeset()
            changeset_id = changeset.id
            try:
                url = reverse(
                    'schemanizer_confirm_soft_delete_changeset',
                    args=[changeset_id])
                if changeset.can_be_soft_deleted_by(user):
                    r = c.post(url, data=dict(confirm_soft_delete='Submit'))
                    tmp_changeset = models.Changeset.objects.get(pk=changeset_id)
                    self.assertTrue(tmp_changeset.is_deleted)
            finally:
                businesslogic.delete_changeset(changeset)

    def test_changeset_update(self):
        """Tests changeset update."""
        c = Client()
        for u, p in self.users:
            self._login(c, u, p)
            user = models.User.objects.get(name=u)
            changeset = self._create_changeset()
            changeset_id = changeset.id
            try:
                url = reverse('schemanizer_update_changeset', args=[changeset_id])
                r = c.get(url)

                self.assertTrue(r.context['user_has_access'])
                if changeset.can_be_updated_by(user):
                    self.assertTrue('changeset_form' in r.context)
                    self.assertTrue('changeset_detail_formset' in r.context)
            finally:
                businesslogic.delete_changeset(changeset_id)

    def test_changeset_update_post(self):
        """Tests changeset update posts."""
        c = Client()
        for u, p in self.users:
            self._login(c, u, p)
            user = models.User.objects.get(name=u)
            changeset = self._create_changeset()
            changeset_id = changeset.id
            try:
                changeset_detail = changeset.changeset_details.all()[0]
                url = reverse('schemanizer_update_changeset', args=[changeset_id])
                if changeset.can_be_updated_by(user):
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

    def test_changeset_apply_continue_form_submit(self):
        """Tests changeset apply."""

        database_schema_id = 4
        schema_version_id = 4
        changeset_id = 15
        database_schema = models.DatabaseSchema.objects.get(pk=database_schema_id)
        c = Client()
        for u, p in self.users:
            self._login(c, u, p)
            url = reverse('schemanizer_changeset_apply')
            query_string = urllib.urlencode(dict(
                database_schema_id=database_schema_id,
                schema_version_id=schema_version_id,
                changeset_id=changeset_id))
            data = dict(continue_form_submit='Submit')

            if u in ('dba',):
                r = c.post('%s?%s' % (url, query_string), data=data)
                try:
                    self.assertTrue(models.ChangesetDetailApply.objects.get_by_schema_version_changeset(
                        schema_version_id=schema_version_id,
                        changeset_id=changeset_id).exists())
                finally:
                    models.ChangesetDetailApply.objects.get_by_schema_version_changeset(
                        schema_version_id=schema_version_id,
                        changeset_id=changeset_id).delete()

                    if settings.DEV_NO_EC2_APPLY_CHANGESET:
                        conn = businesslogic.create_aws_mysql_connection(
                            db=database_schema.name)
                        with conn as cursor:
                            cursor.execute('drop schema %s;' % (database_schema.name,))
