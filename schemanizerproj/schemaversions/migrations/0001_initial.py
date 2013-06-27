# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'DatabaseSchema'
        db.create_table('database_schemas', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=255)),
        ))
        db.send_create_signal(u'schemaversions', ['DatabaseSchema'])

        # Adding model 'SchemaVersion'
        db.create_table('schema_versions', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
            ('database_schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemaversions.DatabaseSchema'])),
            ('ddl', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
            ('checksum', self.gf('django.db.models.fields.CharField')(default='', max_length=255, blank=True)),
            ('pulled_from', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='pulled_from', default=None, to=orm['servers.Server'], blank=True, null=True)),
            ('pull_datetime', self.gf('django.db.models.fields.DateTimeField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'schemaversions', ['SchemaVersion'])

        # Adding unique constraint on 'SchemaVersion', fields ['database_schema', 'checksum']
        db.create_unique('schema_versions', ['database_schema_id', 'checksum'])


    def backwards(self, orm):
        # Removing unique constraint on 'SchemaVersion', fields ['database_schema', 'checksum']
        db.delete_unique('schema_versions', ['database_schema_id', 'checksum'])

        # Deleting model 'DatabaseSchema'
        db.delete_table('database_schemas')

        # Deleting model 'SchemaVersion'
        db.delete_table('schema_versions')


    models = {
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
        }
    }

    complete_apps = ['schemaversions']