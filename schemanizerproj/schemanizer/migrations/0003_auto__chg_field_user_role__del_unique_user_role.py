# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'User', fields ['role']
        db.delete_unique('users', ['role_id'])


        # Changing field 'User.role'
        db.alter_column('users', 'role_id', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemanizer.Role'], null=True, db_column='role_id'))

    def backwards(self, orm):

        # Changing field 'User.role'
        db.alter_column('users', 'role_id', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['schemanizer.Role'], unique=True, null=True, db_column='role_id'))
        # Adding unique constraint on 'User', fields ['role']
        db.create_unique('users', ['role_id'])


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
            'approved_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'approved_by': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'approved_changesets'", 'null': 'True', 'db_column': "'approved_by'", 'to': u"orm['schemanizer.User']"}),
            'classification': ('django.db.models.fields.CharField', [], {'default': "u'painless'", 'max_length': '10', 'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
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
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'new'", 'max_length': '6', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemanizer.changesetdetail': {
            'Meta': {'object_name': 'ChangesetDetail', 'db_table': "'changeset_details'"},
            'after_checksum': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'apply_sql': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'before_checksum': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'changeset': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemanizer.Changeset']", 'null': 'True', 'db_column': "'changeset_id'", 'blank': 'True'}),
            'count_sql': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'revert_sql': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'type': ('django.db.models.fields.CharField', [], {'default': "u'add'", 'max_length': '6', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'volumetric_values': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        u'schemanizer.role': {
            'Meta': {'object_name': 'Role', 'db_table': "'roles'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        },
        u'schemanizer.user': {
            'Meta': {'object_name': 'User', 'db_table': "'users'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'role': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemanizer.Role']", 'null': 'True', 'db_column': "'role_id'", 'blank': 'True'}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'schemanizer_user'", 'unique': 'True', 'db_column': "'auth_user_id'", 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['schemanizer']