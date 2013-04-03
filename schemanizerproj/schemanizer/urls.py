from django.conf.urls import patterns, url

urlpatterns = patterns('schemanizer.views',
    url(r'^$', 'home', name='schemanizer_home'),

    url(r'^users/$', 'users', name='schemanizer_users'),

    url(r'^changesets/$', 'changesets', name='schemanizer_changesets'),
    url(r'^changeset/(?P<id>\d+)/$', 'changeset_view', name='schemanizer_changeset_view'),
    url(r'^changeset/submit/$', 'changeset_submit', name='schemanizer_changeset_submit'),
    url(r'^changeset/review/(?P<id>\d+)/$', 'changeset_review', name='schemanizer_changeset_review'),


)