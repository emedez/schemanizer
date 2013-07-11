from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',
    #
    # Database Schema
    #
    url(
        r'^database-schema/list/', views.DatabaseSchemaList.as_view(),
        name='schemaversions_database_schema_list'),

    #
    # Schema Version
    #
    url(
        r'^schema-version/list/', views.SchemaVersionList.as_view(),
        name='schemaversions_schema_version_list'),
    url(
        r'^schema-version/generate/(?P<server_pk>\d+)/',
        views.SchemaVersionGenerate.as_view(),
        name='schemaversions_schema_version_generate'),
    url(
        r'^schema-version/(?P<pk>\d+)/$', views.SchemaVersion.as_view(),
        name='schemaversions_schema_version'),
    url(
        r'^schema-version/download-ddl/(?P<schema_version_pk>\d+)/$',
        views.SchemaVersionDdlDownload.as_view(),
        name='schemaversions_schema_version_download_ddl'),
    url(
        r'^ajax-get-schema-version/$',
        'schemaversions.views.ajax_get_schema_version',
        name='schemaversions_ajax_get_schema_version'),

    #
    # schema check
    #
    url(
        r'^schema-check/(?P<database_schema_pk>\d+)/$',
        'schemaversions.views.schema_check',
        name='schemaversions_schema_check'
    )
)