from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',
    #
    # User
    #
    url(r'^user/list/', views.UserList.as_view(), name='users_user_list'),
    url(r'^user/add/$', views.UserAdd.as_view(), name='users_user_add'),
    url(
        r'^user/update/(?P<pk>\d+)/$', views.UserUpdate.as_view(),
        name='users_user_update'),
    url(
        r'^user/delete/(?P<pk>\d+)/$', views.UserDelete.as_view(),
        name='users_user_delete'),
)
