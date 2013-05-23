import json
import logging
from pprint import pformat
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import connection, transaction
from django.test import TestCase, Client, TransactionTestCase
from django.utils import timezone

from tastypie.test import ResourceTestCase

from schemanizer import exceptions, models, utils
from schemanizer import businesslogic
from schemanizer.logic import (
    privileges as logic_privileges,
    changeset_review as logic_changeset_review,
    user as logic_user)

log = logging.getLogger(__name__)

class ChangesetReviewLogicTest(TransactionTestCase):
    fixtures = ['schemanizer/test.yaml']

    def setUp(self):
        super(ChangesetReviewLogicTest, self).setUp()

        # usernames and passwords
        self.users = (
            ('dev', 'dev'),
            ('dba', 'dba'),
            ('admin', 'admin')
        )

    def _login(self, client, username, password):
        logged_in = client.login(username=username, password=password)
        self.assertTrue(logged_in)

    def _create_changeset(self, database_schema):
        user = models.User.objects.get(name='dev')
        changeset = models.Changeset.objects.create(
            database_schema=database_schema,
            type=models.Changeset.DDL_TABLE_CREATE,
            classification=models.Changeset.CLASSIFICATION_PAINLESS,
            review_status=models.Changeset.REVIEW_STATUS_NEEDS,
            submitted_by=user,
            submitted_at=timezone.now())
        models.ChangesetDetail.objects.create(
            changeset=changeset,
            type=models.ChangesetDetail.TYPE_ADD,
            description='create table t2',
            apply_sql="""
                create table `t2` (
                    `id` int primary key auto_increment,
                    `name` varchar(255)
                )
                """,
            revert_sql="""
                drop table `t2`
                """)
        models.ChangesetDetail.objects.create(
            changeset=changeset,
            type=models.ChangesetDetail.TYPE_UPD,
            description='test update data',
            apply_sql="""
                update t1 set id = 9999 where id = 9999;
                """,
            revert_sql='')
        log.info('Changeset [id=%s] was created.' % (changeset.id,))
        return changeset

    def test_changeset_review(self):
        log.debug('__name__ = %s' % (__name__,))
        schema_name = 'schemanizer_test_changeset_review'
        database_schema = models.DatabaseSchema.objects.create(
            name=schema_name
        )
        ddl = """
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `t1` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `varchar_1` varchar(255) DEFAULT NULL,
  `int_1` int(11) DEFAULT NULL,
  `int_2` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=latin1;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
        """
        schema_version = models.SchemaVersion.objects.create(
            database_schema=database_schema,
            ddl=ddl,
            checksum=utils.schema_hash(ddl)
        )

        #c = Client()
        for u, p in self.users:
            #self._login(c, u, p)
            #log.debug('%s logged in.' % (u,))

            user = models.User.objects.get(name=u)

            try:
#                cursor = connection.cursor()
#                cursor.execute('drop schema if exists %s' % (schema_name,))
#                while cursor.nextset() is not None:
#                    pass
#                log.debug('%s was dropped (if exists).' % (schema_name,))

                changeset = self._create_changeset(database_schema)

                #user_has_access = businesslogic.changeset_can_be_reviewed_by_user(
                #    changeset, user)
                changeset_review = logic_changeset_review.ChangesetReview(
                    changeset, schema_version, user)
                if u == 'dev':
                    self.assertRaises(
                        exceptions.PrivilegeError, changeset_review.run)
                else:
                    changeset_review.run()
#                url = reverse('schemanizer_changeset_review', args=[changeset_id])
#                r = c.get(url)
#                if u in ('dba', 'admin'):
#                    self.assertTrue(user_has_access)
#                else:
#                    self.assertFalse(user_has_access)
#                if user_has_access:
#                    self.assertTrue('select_schema_version_form' in r.context)
#
#                log.debug('Review thread section (dba-only).')
#                if u in ('dba', ):
#                    r = c.get(url, data=dict(schema_version=schema_version_id))
#                    if user_has_access:
#                        self.assertTrue('thread' in r.context)
#                        self.assertTrue(r.context['thread_started'])
#                        thread = r.context['thread']
#                        # wait for thread to end
#                        log.debug('Waiting for review thread to end...')
#                        thread.join()
#                        log.debug('Review thread ended.')

            except:
                log.exception('EXCEPTION')
                raise
#            finally:
#                if schema_version:
#                    schema_version.delete()
#                    log.debug('Schema version was deleted.')
#                if changeset:
#                    changeset.delete()
#                    log.debug('Changeset was deleted.')
#        database_schema.delete()
#        log.debug('Database schema [id=%s] was deleted.' % (
#            database_schema_id,))
#
#        log.debug('=' * 80)


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

        self.admin_user = models.User.objects.get(name='admin')

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
                logic_user.delete_user(self.admin_user, created_user)
            else:
                self.assertFalse(r.context['user_has_access'])

    def _create_user_dev(self):
        user = models.User.objects.get(name='admin')
        role = models.Role.objects.get(name=models.Role.ROLE_DEVELOPER)
        created_user = logic_user.create_user(
            user=user,
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
            logic_user.delete_user(self.admin_user, created_user_id)

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
            logic_user.delete_user(self.admin_user, created_user_id)

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
            logic_user.delete_user(self.admin_user, created_user_id)

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
                user_privileges = logic_privileges.UserPrivileges(user)
                can_update = businesslogic.changeset_can_be_updated_by_user(
                    changeset, user)
                can_set_review_status_to_in_progress = businesslogic.changeset_can_be_reviewed_by_user(
                    changeset, user)
                can_approve = businesslogic.changeset_can_be_approved_by_user(
                    changeset, user)
                can_reject = businesslogic.changeset_can_be_rejected_by_user(
                    changeset, user)
                can_soft_delete = user_privileges.can_soft_delete_changeset(
                    changeset)
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

                logic_privileges.UserPrivileges(
                    user).check_soft_delete_changeset(changeset)

                r = c.post(url, data=dict(confirm_soft_delete='Submit'))
                tmp_changeset = models.Changeset.objects.get(pk=changeset_id)
                self.assertTrue(tmp_changeset.is_deleted)
            finally:
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
        schema_name = 'schemanizer_test_schema'
        cursor = connection.cursor()
        cursor.execute('create schema if not exists %s' % (schema_name,))
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
                data = dict(schema=schema_name)
                r = c.post(url, data)

                self.assertRedirects(r, reverse('schemanizer_server_list'))
        finally:
            server.delete()

    def test_schema_version_view(self):
        database_schema = None
        schema_version = None
        try:
            database_schema = models.DatabaseSchema.objects.create(
                name='schemanizer_test_schema')
            schema_version = models.SchemaVersion.objects.create(
                database_schema=database_schema, ddl='',
                checksum=utils.schema_hash(''))
            url = reverse(
                'schemanizer_schema_version_view', args=[schema_version.id])
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


class RestApiTest(ResourceTestCase):
    """Tests for Schemanizer REST API."""

    fixtures = ['schemanizer/test.yaml']

    def setUp(self):
        super(RestApiTest, self).setUp()

    def get_admin_credentials(self):
        """Returns admin credentials."""
        return self.create_basic(username='admin', password='admin')

    def get_dba_credentials(self):
        return self.create_basic(username='dba', password='dba')

    def get_developer_credentials(self):
        """Returns developer credentials."""
        return self.create_basic(username='dev', password='dev')

    def create_database_schema(self):
        database_schema = models.DatabaseSchema.objects.create(
            name='schemanizer_test_schema_1')
        return database_schema

    def create_changeset(self):
        database_schema = self.create_database_schema()
        changeset = models.Changeset.objects.create(
            database_schema=database_schema, type='DDL:Table:Create',
            classification='painless',
            submitted_by=models.User.objects.get(name='dev'),
            submitted_at=timezone.now())
        return changeset

    def test_user_create(self):
        current_user_count = models.User.objects.count()
        post_data = dict(
            name='dev2',
            email='dev2@example.com',
            role_id=models.Role.objects.get(name='developer').pk,
            password='dev2'
        )
        resp = self.api_client.post(
            '/api/v1/user/create/', format='json', data=post_data,
            authentication=self.get_admin_credentials())
        log.debug('status_code = %s' % (resp.status_code,))
        log.debug(resp.content)
        self.assertEqual(models.User.objects.count(), current_user_count + 1)

        # Scenario: Developer attempts to create user.
        resp = self.api_client.post(
            '/api/v1/user/create/', format='json', data=post_data,
            authentication=self.get_developer_credentials())
        log.debug('status_code = %s' % (resp.status_code,))
        log.debug(resp.content)
        obj = json.loads(resp.content)
        self.assertEqual(
            obj['error_message'],
            logic_privileges.MSG_CREATE_USER_NOT_ALLOWED)

    def test_submit_changeset(self):
        database_schema = self.create_database_schema()
        post_data = dict(
            changeset=dict(
                database_schema_id=database_schema.id,
                type='DDL:Table:Create',
                classification='painless',
                version_control_url=''
            ),
            changeset_details=[
                dict(
                    type='add',
                    description='create_a_table',
                    apply_sql='create table t1 (id int primary key auto_increment)',
                    revert_sql='drop table t1'
                )
            ]
        )
        submit_changeset_url = '/api/v1/changeset/submit/'
        resp = self.api_client.post(
            submit_changeset_url, format='json', data=post_data,
            authentication=self.get_developer_credentials())
        log.debug('status_code = %s' % (resp.status_code,))
        log.debug(resp.content)
        obj = json.loads(resp.content)
        self.assertTrue('id' in obj)

    def test_reject_changeset(self):
        #database_schema = models.DatabaseSchema.objects.create(
        #    name='schemanizer_test_schema_1')
        #changeset = models.Changeset.objects.create(
        #    database_schema=database_schema, type='DDL:Table:Create',
        #    classification='painless')
        changeset = self.create_changeset()

        reject_changeset_url='/api/v1/changeset/reject/%s/' % (changeset.id,)
        resp = self.api_client.post(
            reject_changeset_url, format='json',
            authentication=self.get_dba_credentials())
        log.debug('status_code = %s' % (resp.status_code,))
        log.debug(resp.content)
        obj = json.loads(resp.content)
        self.assertEquals(obj['id'], changeset.id)
        self.assertEquals(obj['review_status'], 'rejected')

    def test_approve_changeset(self):
        changeset = self.create_changeset()
        changeset.review_status = 'in_progress'
        changeset.save()

        approve_changeset_url='/api/v1/changeset/approve/%s/' % (changeset.id,)
        resp = self.api_client.post(
            approve_changeset_url, format='json',
            authentication=self.get_dba_credentials())
        log.debug('status_code = %s' % (resp.status_code,))
        log.debug(resp.content)
        obj = json.loads(resp.content)
        self.assertEquals(obj['id'], changeset.id)
        self.assertEquals(obj['review_status'], 'approved')

    def test_soft_delete_changeset(self):
        changeset = self.create_changeset()
        soft_delete_changeset_url = '/api/v1/changeset/soft_delete/%s/' % (changeset.id,)
        resp = self.api_client.post(
            soft_delete_changeset_url, format='json',
            authentication=self.get_dba_credentials()
        )
        log.debug('status_code = %s' % (resp.status_code,))
        log.debug(resp.content)
        obj = json.loads(resp.content)
        self.assertEquals(obj['id'], changeset.id)
        self.assertEquals(obj['is_deleted'], 1)

