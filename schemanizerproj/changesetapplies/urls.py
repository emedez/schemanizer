from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',
    url(
        r'^changeset-apply/(?P<changeset_pk>\d+)/',
        'changesetapplies.views.changeset_apply',
        name='changesetapplies_changeset_apply'),
    url(
        r'^select-environment-servers/$',
        'changesetapplies.views.select_environment_servers',
        name='changesetapplies_select_environment_servers'),
    url(
        r'^apply-to-multiple-hosts/(?P<changeset_pk>\d+)/$',
        'changesetapplies.views.apply_changeset_to_multiple_hosts',
        name='changesetapplies_apply_changesets_to_multiple_hosts'),
    url(
        r'^changeset-applies/',
        'changesetapplies.views.changeset_applies',
        name='changesetapplies_changeset_applies'),
    url(
        r'^ajax-changeset-applies/',
        'changesetapplies.views.ajax_changeset_applies',
        name='changesetapplies_ajax_changeset_applies'),
)
