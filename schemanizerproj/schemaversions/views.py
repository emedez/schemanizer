import StringIO
import json
import logging
import urllib
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import ListView, FormView, DetailView, View
from utils import decorators
from servers import models as servers_models
from . import (
    models, user_access, forms, schema_functions, event_handlers)

log = logging.getLogger(__name__)
MSG_USER_NO_ACCESS = u'You do not have access to this page.'
MSG_NOT_AJAX = u'Request must be a valid XMLHttpRequest.'


class DatabaseSchemaList(ListView):
    model = models.DatabaseSchema

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(DatabaseSchemaList, self).dispatch(
            request, *args, **kwargs)


class SchemaVersionList(ListView):
    model = models.SchemaVersion

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(SchemaVersionList, self).dispatch(
            request, *args, **kwargs)


class SchemaVersionGenerate(FormView):
    template_name = 'schemaversions/schemaversion_generate.html'
    form_class = forms.SchemaVersionGenerateForm
    success_url = reverse_lazy('servers_server_list')

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(SchemaVersionGenerate, self).dispatch(
            request, *args, **kwargs)

    def get_form(self, form_class):
        form = super(SchemaVersionGenerate, self).get_form(form_class)
        self.server = servers_models.Server.objects.get(
            pk=int(self.kwargs['server_pk']))
        connection_options = {
            'user': settings.MYSQL_USER,
            'passwd': settings.MYSQL_PASSWORD
        }
        form.fields['schema'].choices = [
            (schema, schema)
            for schema in self.server.get_schema_list(connection_options)]
        return form

    def form_valid(self, form):
        schema_name = form.cleaned_data['schema']
        connection_options = {
            'user': settings.MYSQL_USER,
            'passwd': settings.MYSQL_PASSWORD
        }
        schema_version, schema_version_created = (
            schema_functions.generate_schema_version(
                self.server, schema_name, connection_options))
        event_handlers.on_schema_version_generated(
            self.request, schema_version, schema_version_created)
        return redirect('schemaversions_schema_version', schema_version.pk)
        #return super(SchemaVersionGenerate, self).form_valid(form)


class SchemaVersion(DetailView):
    model = models.SchemaVersion

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(SchemaVersion, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SchemaVersion, self).get_context_data(**kwargs)
        context['actions_form'] = forms.SchemaVersionActionsForm(
            initial=dict(schema_version=int(self.kwargs['pk'])))
        return context

    def post(self, request, *args, **kwargs):
        try:
            if 'schema_check' in request.POST:
                schema_version = self.get_object()
                schema_version.database_schema.generate_server_data(
                    servers=servers_models.Server.objects.all(),
                    connection_options={
                        'user': settings.MYSQL_USER,
                        'passwd': settings.MYSQL_PASSWORD
                    })
                url = reverse('servers_server_data_list')
                params = urllib.urlencode(
                    dict(database_schema_id=schema_version.database_schema.pk))
                event_handlers.on_schema_check(
                    request=request,
                    database_schema=schema_version.database_schema)
                return redirect('%s?%s' % (url, params))
        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            messages.error(request, msg)
            log.exception(msg)
        return self.get(request, *args, **kwargs)


class SchemaVersionDdlDownload(View):

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(SchemaVersionDdlDownload, self).dispatch(
            request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        try:
            schema_version_pk = int(self.kwargs['schema_version_pk'])
            schema_version = models.SchemaVersion.objects.get(
                pk=schema_version_pk)
            ddl_file = StringIO.StringIO()
            ddl_file.write(schema_version.ddl)
            response = HttpResponse(
                FileWrapper(ddl_file), content_type='text/plain')
            response['Content-Disposition'] = (
                'attachment; filename=schema_version_%s.sql' % (
                    schema_version.pk,))
            response['Content-Length'] = ddl_file.tell()
            ddl_file.seek(0)
            return response
        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            log.exception(msg)
            messages.error(request, msg)

        raise Http404


def ajax_get_schema_version(
        request, template='schemaversions/ajax_get_schema_version.html'):
    if not request.is_ajax():
        return HttpResponseForbidden(MSG_NOT_AJAX)

    data = {}
    try:
        if not request.user.is_authenticated():
            raise Exception('Login is required.')

        schema_version_id = request.GET['schema_version_id'].strip()
        if schema_version_id:
            schema_version_id = int(schema_version_id)
            schema_version = models.SchemaVersion.objects.get(
                pk=schema_version_id)
            data['schema_version_html'] = render_to_string(
                template, {'obj': schema_version},
                context_instance=RequestContext(request))
        else:
            data['schema_version_html'] = ''

        data_json = json.dumps(data)
    except Exception, e:
        msg = 'ERROR %s: %s' % (type(e), e)
        log.exception(msg)
        data = dict(error=msg)
        data_json = json.dumps(data)

    return HttpResponse(data_json, mimetype='application/json')