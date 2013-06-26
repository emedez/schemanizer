from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',
    url(
        r'^event/list/', views.EventList.as_view(),
        name='events_event_list'),
)
