# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Changeset'
        db.create_table('changesets', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
            ('database_schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemaversions.DatabaseSchema'])),
            ('type', self.gf('django.db.models.fields.CharField')(default=u'DDL:Table:Create', max_length=17)),
            ('classification', self.gf('django.db.models.fields.CharField')(default=u'painless', max_length=10)),
            ('version_control_url', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('review_status', self.gf('django.db.models.fields.CharField')(default=u'needs', max_length=11, blank=True)),
            ('reviewed_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='reviewed_by', on_delete=models.SET_NULL, default=None, to=orm['users.User'], blank=True, null=True)),
            ('reviewed_at', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('approved_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='approved_by', on_delete=models.SET_NULL, default=None, to=orm['users.User'], blank=True, null=True)),
            ('approved_at', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('submitted_by', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='submitted_by', on_delete=models.SET_NULL, default=None, to=orm['users.User'], blank=True, null=True)),
            ('submitted_at', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
            ('is_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('review_version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='review_version', on_delete=models.SET_NULL, default=None, to=orm['schemaversions.SchemaVersion'], blank=True, null=True)),
            ('before_version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='before_version', on_delete=models.SET_NULL, default=None, to=orm['schemaversions.SchemaVersion'], blank=True, null=True)),
            ('after_version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='after_version', on_delete=models.SET_NULL, default=None, to=orm['schemaversions.SchemaVersion'], blank=True, null=True)),
            ('repo_filename', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal(u'changesets', ['Changeset'])

        # Adding model 'ChangesetDetail'
        db.create_table('changeset_details', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
            ('changeset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['changesets.Changeset'])),
            ('description', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('apply_sql', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('revert_sql', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('before_checksum', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('after_checksum', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('apply_verification_sql', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('revert_verification_sql', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('volumetric_values', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal(u'changesets', ['ChangesetDetail'])

        # Adding model 'ChangesetAction'
        db.create_table('changeset_actions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('changeset', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['changesets.Changeset'])),
            ('type', self.gf('django.db.models.fields.CharField')(default=u'created', max_length=34, null=True, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'changesets', ['ChangesetAction'])

        # Adding model 'ChangesetActionServerMap'
        db.create_table('changeset_action_server_map', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('changeset_action', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['changesets.ChangesetAction'])),
            ('server', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['servers.Server'])),
        ))
        db.send_create_signal(u'changesets', ['ChangesetActionServerMap'])


    def backwards(self, orm):
        # Deleting model 'Changeset'
        db.delete_table('changesets')

        # Deleting model 'ChangesetDetail'
        db.delete_table('changeset_details')

        # Deleting model 'ChangesetAction'
        db.delete_table('changeset_actions')

        # Deleting model 'ChangesetActionServerMap'
        db.delete_table('changeset_action_server_map')


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
        u'changesets.changeset': {
            'Meta': {'object_name': 'Changeset', 'db_table': "'changesets'"},
            'after_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'after_version'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['schemaversions.SchemaVersion']", 'blank': 'True', 'null': 'True'}),
            'approved_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'approved_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'approved_by'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['users.User']", 'blank': 'True', 'null': 'True'}),
            'before_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'before_version'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['schemaversions.SchemaVersion']", 'blank': 'True', 'null': 'True'}),
            'classification': ('django.db.models.fields.CharField', [], {'default': "u'painless'", 'max_length': '10'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'database_schema': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemaversions.DatabaseSchema']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'repo_filename': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'review_status': ('django.db.models.fields.CharField', [], {'default': "u'needs'", 'max_length': '11', 'blank': 'True'}),
            'review_version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'review_version'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['schemaversions.SchemaVersion']", 'blank': 'True', 'null': 'True'}),
            'reviewed_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'reviewed_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'reviewed_by'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['users.User']", 'blank': 'True', 'null': 'True'}),
            'submitted_at': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'submitted_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'submitted_by'", 'on_delete': 'models.SET_NULL', 'default': 'None', 'to': u"orm['users.User']", 'blank': 'True', 'null': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'DDL:Table:Create'", 'max_length': '17'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'version_control_url': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        u'changesets.changesetaction': {
            'Meta': {'object_name': 'ChangesetAction', 'db_table': "'changeset_actions'"},
            'changeset': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['changesets.Changeset']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'created'", 'max_length': '34', 'null': 'True', 'blank': 'True'})
        },
        u'changesets.changesetactionservermap': {
            'Meta': {'object_name': 'ChangesetActionServerMap', 'db_table': "'changeset_action_server_map'"},
            'changeset_action': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['changesets.ChangesetAction']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['servers.Server']"})
        },
        u'changesets.changesetdetail': {
            'Meta': {'object_name': 'ChangesetDetail', 'db_table': "'changeset_details'"},
            'after_checksum': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'apply_sql': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'apply_verification_sql': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'before_checksum': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'changeset': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['changesets.Changeset']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'revert_sql': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'revert_verification_sql': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'volumetric_values': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'schemaversions.databaseschema': {
            'Meta': {'object_name': 'DatabaseSchema', 'db_table': "'database_schemas'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemaversions.schemaversion': {
            'Meta': {'unique_together': "(('database_schema', 'checksum'),)", 'object_name': 'SchemaVersion', 'db_table': "'schema_versions'"},
            'checksum': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'database_schema': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemaversions.DatabaseSchema']"}),
            'ddl': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pull_datetime': ('django.db.models.fields.DateTimeField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'pulled_from': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'pulled_from'", 'default': 'None', 'to': u"orm['servers.Server']", 'blank': 'True', 'null': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'servers.environment': {
            'Meta': {'object_name': 'Environment', 'db_table': "'environments'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'servers.server': {
            'Meta': {'object_name': 'Server', 'db_table': "'servers'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'environment': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['servers.Environment']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'hostname': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '255'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '255'}),
            'port': ('django.db.models.fields.IntegerField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'users.role': {
            'Meta': {'object_name': 'Role', 'db_table': "'roles'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'developer'", 'max_length': '255'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'users.user': {
            'Meta': {'object_name': 'User', 'db_table': "'users'"},
            'auth_user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'schemanizer_user'", 'unique': 'True', 'to': u"orm['auth.User']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255'}),
            'github_login': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['users.Role']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['changesets']