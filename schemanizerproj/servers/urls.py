from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',
    #
    # Environment
    #
    url(
        r'^environment/list/', views.EnvironmentList.as_view(),
        name='servers_environment_list'),
    url(
        r'^environment/add/$', views.EnvironmentCreate.as_view(),
        name='servers_environment_add'),
    url(
        r'^environment/update/(?P<pk>\d+)/$',
        views.EnvironmentUpdate.as_view(),
        name='servers_environment_update'),
    url(
        r'^environment/delete/(?P<pk>\d+)/$',
        views.EnvironmentDelete.as_view(),
        name='servers_environment_delete'),

    #
    # Server
    #
    url(
        r'^server/list/', views.ServerList.as_view(),
        name='servers_server_list'),
    url(
        r'^server/add/$', views.ServerCreate.as_view(),
        name='servers_server_add'),
    url(
        r'^server/update/(?P<pk>\d+)/$', views.ServerUpdate.as_view(),
        name='servers_server_update'),
    url(
        r'^server/delete/(?P<pk>\d+)/$', views.ServerDelete.as_view(),
        name='servers_server_delete'),

    #
    # ServerData
    #
    url(
        r'^server-data/list/$', views.ServerDataList.as_view(),
        name='servers_server_data_list'),
    url(
        r'^server-data/(?P<pk>\d+)/$', views.ServerData.as_view(),
        name='servers_server_data'),

    # MySQL server discovery
    url(
        r'^discover-mysql-servers/$', views.DiscoverMySqlServers.as_view(),
        name='servers_discover_mysql_servers'),

)
