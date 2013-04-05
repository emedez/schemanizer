from django.conf.urls import patterns, url

urlpatterns = patterns('schemanizer.views',
    url(r'^$', 'home', name='schemanizer_home'),

    url(r'^users/$', 'users', name='schemanizer_users'),
    url(r'^user_create/$', 'user_create', name='schemanizer_user_create'),
    url(r'^update_user/(?P<id>\d+)/$', 'update_user', name='schemanizer_update_user'),
    url(r'^confirm_delete_user/(?P<id>\d+)/$', 'confirm_delete_user', name='schemanizer_confirm_delete_user'),

    url(r'^changesets/$', 'changesets', name='schemanizer_changesets'),
    url(r'^changeset/(?P<id>\d+)/$', 'changeset_view', name='schemanizer_changeset_view'),
    url(r'^changeset/submit/$', 'changeset_submit', name='schemanizer_changeset_submit'),
    url(r'^changeset/review/(?P<id>\d+)/$', 'changeset_review', name='schemanizer_changeset_review'),
    url(r'^changeset/soft_delete/(?P<id>\d+)/$', 'confirm_soft_delete_changeset', name='schemanizer_confirm_soft_delete_changeset'),
    url(r'^apply-changesets/$', 'apply_changesets', name='schemanizer_apply_changesets'),
)