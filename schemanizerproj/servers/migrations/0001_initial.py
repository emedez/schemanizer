# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Environment'
        db.create_table('environments', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', max_length=255)),
        ))
        db.send_create_signal(u'servers', ['Environment'])

        # Adding model 'Server'
        db.create_table('servers', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(default='', unique=True, max_length=255)),
            ('hostname', self.gf('django.db.models.fields.CharField')(default='', max_length=255)),
            ('environment', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['servers.Environment'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('port', self.gf('django.db.models.fields.IntegerField')(default=None, null=True, blank=True)),
        ))
        db.send_create_signal(u'servers', ['Server'])

        # Adding model 'ServerData'
        db.create_table('server_data', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, null=True, blank=True)),
            ('updated_at', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, null=True, blank=True)),
            ('server', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['servers.Server'])),
            ('database_schema', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['schemaversions.DatabaseSchema'])),
            ('schema_exists', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('schema_version', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['schemaversions.SchemaVersion'], null=True, on_delete=models.SET_NULL, blank=True)),
            ('schema_version_diff', self.gf('django.db.models.fields.TextField')(default='', blank=True)),
        ))
        db.send_create_signal(u'servers', ['ServerData'])

        # Adding unique constraint on 'ServerData', fields ['server', 'database_schema']
        db.create_unique('server_data', ['server_id', 'database_schema_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'ServerData', fields ['server', 'database_schema']
        db.delete_unique('server_data', ['server_id', 'database_schema_id'])

        # Deleting model 'Environment'
        db.delete_table('environments')

        # Deleting model 'Server'
        db.delete_table('servers')

        # Deleting model 'ServerData'
        db.delete_table('server_data')


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
            'checksum': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
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
        u'servers.serverdata': {
            'Meta': {'unique_together': "(('server', 'database_schema'),)", 'object_name': 'ServerData', 'db_table': "'server_data'"},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'database_schema': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['schemaversions.DatabaseSchema']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'schema_exists': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'schema_version': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': u"orm['schemaversions.SchemaVersion']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'schema_version_diff': ('django.db.models.fields.TextField', [], {'default': "''", 'blank': 'True'}),
            'server': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['servers.Server']"}),
            'updated_at': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['servers']