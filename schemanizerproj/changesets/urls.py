from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',
    #
    # Changeset
    #
    url(
        r'^changeset/list/$', views.ChangesetList.as_view(),
        name='changesets_changeset_list'),
    url(
        r'^changeset/submit/$', views.ChangesetSubmit.as_view(),
        name='changesets_changeset_submit'),
    url(
        r'^changeset/(?P<id>\d+)/$', 'changesets.views.changeset_view',
        name='changesets_changeset_view'),
    url(
        r'^changeset/update/(?P<pk>\d+)/$',
        views.ChangesetUpdate.as_view(),
        name='changesets_changeset_update'),
    url(
        r'^changeset/delete/(?P<pk>\d+)/$',
        'changesets.views.changeset_soft_delete',
        name='changesets_changeset_soft_delete'),
)