from django.conf.urls import patterns, url

urlpatterns = patterns('schemanizer.views',
    url(r'^$', 'home', name='schemanizer_home'),

    #
    # changeset
    #
    # url(
    #     r'^changeset/(?P<id>\d+)/$', 'changeset_view',
    #     name='schemanizer_changeset_view'),
    # url(r'^changeset/delete/(?P<id>\d+)/$', 'changeset_soft_delete', name='schemanizer_changeset_soft_delete'),
    # url(r'^changeset/update/(?P<id>\d+)/$', 'changeset_update', name='schemanizer_changeset_update'),
    # url(
    #     r'^changeset/apply/(?P<changeset_id>\d+)/', 'changeset_apply',
    #     name='schemanizer_changeset_apply'),
    # url(
    #     r'^changeset/apply-to-multiple-hosts/(?P<changeset_id>\d+)/$',
    #     'apply_changeset_to_multiple_hosts',
    #     name='schemanizer_apply_changesets_to_multiple_hosts'),

    # url(r'^changeset/apply-status/(?P<request_id>.+?)/$', 'changeset_apply_status', name='schemanizer_changeset_apply_status'),
    #url(r'^changeset/validate-syntax/(?P<id>\d+)/', 'changeset_validate_syntax', name='schemanizer_changeset_validate_syntax'),
    #url(r'^changeset/validate-syntax-status/(?P<request_id>.+?)/$', 'changeset_validate_syntax_status', name='schemanizer_changeset_validate_syntax_status'),
    #url(r'^changeset/validate-no-update-with-where-clause/(?P<id>\d+)/$', 'changeset_validate_no_update_with_where_clause', name='schemanizer_changeset_validate_no_update_with_where_clause'),
    # url(
    #     r'^changeset/view-review-results/(?P<changeset_id>\d+)/',
    #     'changeset_view_review_results',
    #     name='schemanizer_changeset_view_review_results'),
    # url(r'^changeset/review/(?P<changeset_id>\d+)/', 'changeset_review', name='schemanizer_changeset_review'),
    # url(r'^changeset/review-status/(?P<request_id>.+?)/$', 'changeset_review_status', name='schemanizer_changeset_review_status'),

    #
    # server
    #
    # url(r'^server/list/$', 'server_list', name='schemanizer_server_list'),
    # url(r'^server/create/$', 'server_update', name='schemanizer_server_create'),
    # url(r'^server/update/(?P<id>\d+)/$', 'server_update', name='schemanizer_server_update'),
    # url(r'^server/delete/(?P<id>\d+)/$', 'server_delete', name='schemanizer_server_delete'),
    # url(r'^server/discover/$', 'server_discover', name='schemanizer_server_discover'),

    #
    # schema version
    #
    # url(r'^schema-version/create/(?P<server_id>\d+)/$', 'schema_version_create', name='schemanizer_schema_version_create'),
    # url(r'^schema-version/list/', 'schema_version_list', name='schemanizer_schema_version_list'),
    # url(r'^schema-version/view/(?P<schema_version_id>\d+)/$', 'schema_version_view', name='schemanizer_schema_version_view'),
    # url(
    #     r'^ajax/get-schema-version/$',
    #     'ajax_get_schema_version',
    #     name='schemanizer_ajax_get_schema_version'),

    #
    # database schema
    #
    # url(r'^database-schema/list/$', 'database_schema_list', name='schemanizer_database_schema_list'),

    #
    # environments
    #
    # url(
    #     r'^environments/list/$', 'environment_list',
    #     name='schemanizer_environment_list'),
    # url(r'^environments/create/$', 'environment_update', name='schemanizer_environment_create'),
    # url(r'^environments/update/(?P<environment_id>\d+)/$', 'environment_update', name='schemanizer_environment_update'),
    # url(r'^environments/del/(?P<environment_id>\d+)/$', 'environment_del', name='schemanizer_environment_del'),

    #
    # celery tasks
    #
    # url(
    #     r'^changeset-reviews/$', 'changeset_reviews',
    #     name='schemanizer_changeset_reviews'),
    # url(
    #     r'^changeset-applies/', 'changeset_applies',
    #     name='schemanizer_changeset_applies'),

    #
    # ajax views
    #
    # url(
    #     r'^select-environment-servers/$', 'select_environment_servers',
    #     name='schemanizer_select_environment_servers'),
    # url(
    #     r'^ajax-changeset-applies/', 'ajax_changeset_applies',
    #     name='schemanizer_ajax_changeset_applies'),
    # url(
    #     r'^ajax-changeset-reviews/', 'ajax_changeset_reviews',
    #     name='schemanizer_ajax_changeset_reviews'),
)