from django.conf import settings
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from schemanizer.forms import AuthenticationForm

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'schemanizerproj.views.home', name='home'),
    # url(r'^schemanizerproj/', include('schemanizerproj.foo.urls')),
    url(r'^$', 'schemanizer.views.home', name='home'),

    url(r'^schemanizer/', include('schemanizer.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    url(
        r'^accounts/login/$', 'django.contrib.auth.views.login',
        {'authentication_form': AuthenticationForm},
        name='login', ),
    url(
        r'^accounts/logout/$', 'django.contrib.auth.views.logout',
        {'next_page': '/'},
        name='logout'),

)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)