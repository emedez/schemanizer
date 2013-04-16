from django.conf.urls import patterns, url

urlpatterns = patterns('schemanizer.views',
    url(r'^$', 'home', name='schemanizer_home'),

    url(r'^user/list/$', 'users', name='schemanizer_users'),
    url(r'^user/create/$', 'user_create', name='schemanizer_user_create'),
    url(r'^user/update/(?P<id>\d+)/$', 'update_user', name='schemanizer_update_user'),
    url(
        r'^user/delete/(?P<id>\d+)/$',
        'confirm_delete_user',
        name='schemanizer_confirm_delete_user'),

    url(r'^changeset/list/$', 'changeset_list', name='schemanizer_changeset_list'),
    url(
        r'^changeset/(?P<id>\d+)/$',
        'changeset_view',
        name='schemanizer_changeset_view'),
    url(
        r'^changeset/submit/$',
        'changeset_submit',
        name='schemanizer_changeset_submit'),
    url(
        r'^changeset/review/(?P<id>\d+)/$',
        'changeset_review',
        name='schemanizer_changeset_review'),
    url(
        r'^changeset/soft-delete/(?P<id>\d+)/$',
        'confirm_soft_delete_changeset',
        name='schemanizer_confirm_soft_delete_changeset'),
    url(
        r'^changeset/update/(?P<id>\d+)/$',
        'update_changeset',
        name='schemanizer_update_changeset'),
    url(
        r'^changeset/apply-results/(?P<schema_version_id>\d+)/(?P<changeset_id>\d+)/$',
        'changeset_apply_results',
        name='schemanizer_changeset_apply_results'),
    url(
        r'^changeset/view-apply-results/',
        'changeset_view_apply_results',
        name='schemanizer_changeset_view_apply_results'),

    # no $ at the end of pattern so we that we can have GET params
    url(r'^changeset/apply/', 'changeset_apply', name='schemanizer_changeset_apply'),


)