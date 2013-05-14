# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Role'
        db.create_table('roles', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['Role'])

        # Adding model 'User'
        db.create_table('users', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=255, blank=True)),
            ('role', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemanizer.Role'], null=True, db_column='role_id', blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
            ('auth_user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='schemanizer_user', unique=True, db_column='auth_user_id', to=orm['auth.User'])),
        ))
        db.send_create_signal(u'schemanizer', ['User'])

        # Adding model 'Changeset'
        db.create_table('changesets', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('database_schema', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='changesets', null=True, db_column='database_schema_id', to=orm['schemanizer.DatabaseSchema'])),
            ('type', self.gf('django.db.models.fields.CharField')(default=u'DDL:Table:Create', max_length=17, blank=True)),
            ('classification', self.gf('django.db.models.fields.CharField')(default=u'painless', max_length=10, blank=True)),
            ('version_control_url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('review_status', self.gf('django.db.models.fields.CharField')(default=u'needs', max_length=11, blank=True)),
            ('reviewed_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='reviewed_changesets', null=True, db_column='reviewed_by', to=orm['schemanizer.User'])),
            ('reviewed_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('approved_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='approved_changesets', null=True, db_column='approved_by', to=orm['schemanizer.User'])),
            ('approved_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('submitted_by', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='submitted_changesets', null=True, db_column='submitted_by', to=orm['schemanizer.User'])),
            ('submitted_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.IntegerField')(default=0, null=True, blank=True)),
            ('before_version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='before_version', default=None, to=orm['schemanizer.SchemaVersion'], blank=True, null=True)),
            ('after_version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='after_version', default=None, to=orm['schemanizer.SchemaVersion'], blank=True, null=True)),
        ))
        db.send_create_signal(u'schemanizer', ['Changeset'])

        # Adding model 'ChangesetDetail'
        db.create_table('changeset_details', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('changeset', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='changeset_details', null=True, db_column='changeset_id', to=orm['schemanizer.Changeset'])),
            ('type', self.gf('django.db.models.fields.CharField')(default=u'add', max_length=6, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('apply_sql', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('revert_sql', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('before_checksum', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('after_checksum', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('count_sql', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('volumetric_values', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['ChangesetDetail'])

        # Adding model 'ChangesetAction'
        db.create_table('changeset_actions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('changeset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemanizer.Changeset'], null=True, db_column='changeset_id', blank=True)),
            ('type', self.gf('django.db.models.fields.CharField')(default=u'created', max_length=7, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['ChangesetAction'])

        # Adding model 'DatabaseSchema'
        db.create_table('database_schemas', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['DatabaseSchema'])

        # Adding model 'SchemaVersion'
        db.create_table('schema_versions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('database_schema', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='schema_versions', null=True, db_column='database_schema_id', to=orm['schemanizer.DatabaseSchema'])),
            ('ddl', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('checksum', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['SchemaVersion'])

        # Adding model 'Environment'
        db.create_table('environments', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, db_column='update_at', blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['Environment'])

        # Adding model 'Server'
        db.create_table('servers', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, blank=True)),
            ('hostname', self.gf('django.db.models.fields.CharField')(default='', max_length=255)),
            ('cached_size', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
            ('environment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='servers', null=True, db_column='environment_id', to=orm['schemanizer.Environment'])),
            ('port', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['Server'])

        # Adding model 'ChangesetDetailApply'
        db.create_table('changeset_detail_applies', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('changeset_detail', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='changeset_detail_applies', null=True, db_column='changeset_detail_id', to=orm['schemanizer.ChangesetDetail'])),
            ('environment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='environment_changeset_detail_applies', null=True, db_column='environment_id', to=orm['schemanizer.Environment'])),
            ('server', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='server_changeset_detail_applies', null=True, db_column='server_id', to=orm['schemanizer.Server'])),
            ('results_log', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['ChangesetDetailApply'])

        # Adding model 'ValidationType'
        db.create_table('validation_types', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('validation_commands', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['ValidationType'])

        # Adding model 'ChangesetValidation'
        db.create_table('changeset_validations', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('changeset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemanizer.Changeset'], null=True, db_column='changeset_id', blank=True)),
            ('validation_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemanizer.ValidationType'], null=True, db_column='validation_type_id', blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('result', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['ChangesetValidation'])

        # Adding model 'TestType'
        db.create_table('test_types', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255L, blank=True)),
            ('description', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['TestType'])

        # Adding model 'ChangesetTest'
        db.create_table('changeset_tests', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('changeset_detail', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemanizer.ChangesetDetail'], null=True, db_column='changeset_detail_id', blank=True)),
            ('test_type', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemanizer.TestType'], null=True, db_column='test_type_id', blank=True)),
            ('environment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemanizer.Environment'], null=True, db_column='environment_id', blank=True)),
            ('server', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemanizer.Server'], null=True, db_column='server_id', blank=True)),
            ('started_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('ended_at', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('results_log', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemanizer', ['ChangesetTest'])


    def backwards(self, orm):
        # Deleting model 'Role'
        db.delete_table('roles')

        # Deleting model 'User'
        db.delete_table('users')

        # Deleting model 'Changeset'
        db.delete_table('changesets')

        # Deleting model 'ChangesetDetail'
        db.delete_table('changeset_details')

        # Deleting model 'ChangesetAction'
        db.delete_table('changeset_actions')

        # Deleting model 'DatabaseSchema'
        db.delete_table('database_schemas')

        # Deleting model 'SchemaVersion'
        db.delete_table('schema_versions')

        # Deleting model 'Environment'
        db.delete_table('environments')

        # Deleting model 'Server'
        db.delete_table('servers')

        # Deleting model 'ChangesetDetailApply'
        db.delete_table('changeset_detail_applies')

        # Deleting model 'ValidationType'
        db.delete_table('validation_types')

        # Deleting model 'ChangesetValidation'
        db.delete_table('changeset_validations')

        # Deleting model 'TestType'
        db.delete_table('test_types')

        # Deleting model 'ChangesetTest'
        db.delete_table('changeset_tests')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'schemanizer.changeset': {
            'Meta': {'object_name': 'Changeset', 'db_table': "'changesets'"},
            'after_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'after_version'", 'default': 'None', 'to': u"orm['schemanizer.SchemaVersion']", 'blank': 'True', 'null': 'True'}),
            'approved_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'approved_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'approved_changesets'", 'null': 'True', 'db_column': "'approved_by'", 'to': u"orm['schemanizer.User']"}),
            'before_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'before_version'", 'default': 'None', 'to': u"orm['schemanizer.SchemaVersion']", 'blank': 'True', 'null': 'True'}),
            'classification': ('django.db.models.fields.CharField', [], {'default': "u'painless'", 'max_length': '10', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'database_schema': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'changesets'", 'null': 'True', 'db_column': "'database_schema_id'", 'to': u"orm['schemanizer.DatabaseSchema']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True', 'blank': 'True'}),
            'review_status': ('django.db.models.fields.CharField', [], {'default': "u'needs'", 'max_length': '11', 'blank': 'True'}),
            'reviewed_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'reviewed_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'reviewed_changesets'", 'null': 'True', 'db_column': "'reviewed_by'", 'to': u"orm['schemanizer.User']"}),
            'submitted_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'submitted_changesets'", 'null': 'True', 'db_column': "'submitted_by'", 'to': u"orm['schemanizer.User']"}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'DDL:Table:Create'", 'max_length': '17', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'version_control_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'schemanizer.changesetaction': {
            'Meta': {'object_name': 'ChangesetAction', 'db_table': "'changeset_actions'"},
            'changeset': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemanizer.Changeset']", 'null': 'True', 'db_column': "'changeset_id'", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'created'", 'max_length': '7', 'blank': 'True'})
        },
        u'schemanizer.changesetdetail': {
            'Meta': {'object_name': 'ChangesetDetail', 'db_table': "'changeset_details'"},
            'after_checksum': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'apply_sql': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'before_checksum': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'changeset': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'changeset_details'", 'null': 'True', 'db_column': "'changeset_id'", 'to': u"orm['schemanizer.Changeset']"}),
            'count_sql': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'revert_sql': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'add'", 'max_length': '6', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'volumetric_values': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'schemanizer.changesetdetailapply': {
            'Meta': {'object_name': 'ChangesetDetailApply', 'db_table': "'changeset_detail_applies'"},
            'changeset_detail': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'changeset_detail_applies'", 'null': 'True', 'db_column': "'changeset_detail_id'", 'to': u"orm['schemanizer.ChangesetDetail']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'environment_changeset_detail_applies'", 'null': 'True', 'db_column': "'environment_id'", 'to': u"orm['schemanizer.Environment']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'results_log': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'server_changeset_detail_applies'", 'null': 'True', 'db_column': "'server_id'", 'to': u"orm['schemanizer.Server']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemanizer.changesettest': {
            'Meta': {'object_name': 'ChangesetTest', 'db_table': "'changeset_tests'"},
            'changeset_detail': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemanizer.ChangesetDetail']", 'null': 'True', 'db_column': "'changeset_detail_id'", 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'ended_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemanizer.Environment']", 'null': 'True', 'db_column': "'environment_id'", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'results_log': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemanizer.Server']", 'null': 'True', 'db_column': "'server_id'", 'blank': 'True'}),
            'started_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'test_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemanizer.TestType']", 'null': 'True', 'db_column': "'test_type_id'", 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemanizer.changesetvalidation': {
            'Meta': {'object_name': 'ChangesetValidation', 'db_table': "'changeset_validations'"},
            'changeset': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemanizer.Changeset']", 'null': 'True', 'db_column': "'changeset_id'", 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'result': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'validation_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemanizer.ValidationType']", 'null': 'True', 'db_column': "'validation_type_id'", 'blank': 'True'})
        },
        u'schemanizer.databaseschema': {
            'Meta': {'object_name': 'DatabaseSchema', 'db_table': "'database_schemas'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemanizer.environment': {
            'Meta': {'object_name': 'Environment', 'db_table': "'environments'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'db_column': "'update_at'", 'blank': 'True'})
        },
        u'schemanizer.role': {
            'Meta': {'object_name': 'Role', 'db_table': "'roles'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemanizer.schemaversion': {
            'Meta': {'object_name': 'SchemaVersion', 'db_table': "'schema_versions'"},
            'checksum': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'database_schema': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'schema_versions'", 'null': 'True', 'db_column': "'database_schema_id'", 'to': u"orm['schemanizer.DatabaseSchema']"}),
            'ddl': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemanizer.server': {
            'Meta': {'object_name': 'Server', 'db_table': "'servers'"},
            'cached_size': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'servers'", 'null': 'True', 'db_column': "'environment_id'", 'to': u"orm['schemanizer.Environment']"}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'blank': 'True'}),
            'port': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemanizer.testtype': {
            'Meta': {'object_name': 'TestType', 'db_table': "'test_types'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255L', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemanizer.user': {
            'Meta': {'object_name': 'User', 'db_table': "'users'"},
            'auth_user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'schemanizer_user'", 'unique': 'True', 'db_column': "'auth_user_id'", 'to': u"orm['auth.User']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemanizer.Role']", 'null': 'True', 'db_column': "'role_id'", 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemanizer.validationtype': {
            'Meta': {'object_name': 'ValidationType', 'db_table': "'validation_types'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'validation_commands': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['schemanizer']