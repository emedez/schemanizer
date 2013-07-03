from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',
    url(
        r'^changeset-reviews/$', views.ChangesetReviews.as_view(),
        name='changesetreviews_changeset_reviews'),
    url(
        r'^ajax-changeset-reviews/', views.AjaxChangesetReviews.as_view(),
        name='changesetreviews_ajax_changeset_reviews'),
    url(
        r'^changeset-review/(?P<changeset_id>\d+)/$',
        'changesetreviews.views.changeset_review',
        name='changesetreviews_changeset_review'),
    url(
        r'^result/(?P<changeset_id>\d+)/',
        'changesetreviews.views.result',
        name='changesetreviews_result'),
)