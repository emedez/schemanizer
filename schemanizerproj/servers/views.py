import logging
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, TemplateView, DetailView)
from utils import decorators, forms as utils_forms
from . import event_handlers, forms, models, user_access, server_discovery


log = logging.getLogger(__name__)


class EnvironmentList(ListView):
    model = models.Environment

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(EnvironmentList, self).dispatch(request, *args, **kwargs)


class EnvironmentCreate(CreateView):
    model = models.Environment
    form_class = forms.EnvironmentForm
    success_url = reverse_lazy('servers_environment_list')

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(EnvironmentCreate, self).dispatch(
            request, *args, **kwargs)

    def form_valid(self, form):
        return_value = super(EnvironmentCreate, self).form_valid(form)
        event_handlers.on_environment_added(self.request, self.object)
        return return_value


class EnvironmentUpdate(UpdateView):
    model = models.Environment
    form_class = forms.EnvironmentForm
    success_url = reverse_lazy('servers_environment_list')

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(EnvironmentUpdate, self).dispatch(
            request, *args, **kwargs)

    def form_valid(self, form):
        return_value = super(EnvironmentUpdate, self).form_valid(form)
        event_handlers.on_environment_updated(self.request, self.object)
        return return_value


class EnvironmentDelete(DeleteView):
    model = models.Environment
    success_url = reverse_lazy('servers_environment_list')

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(EnvironmentDelete, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(EnvironmentDelete, self).get_context_data(**kwargs)
        context['form'] = utils_forms.SubmitForm()
        return context

    def delete(self, request, *args, **kwargs):
        to_be_deleted_object = self.get_object()
        return_value = super(EnvironmentDelete, self).delete(
            request, *args, **kwargs)
        event_handlers.on_environment_deleted(
            self.request, to_be_deleted_object)
        return return_value


class ServerList(ListView):
    model = models.Server

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(ServerList, self).dispatch(request, *args, **kwargs)


class ServerCreate(CreateView):
    model = models.Server
    form_class = forms.ServerForm
    success_url = reverse_lazy('servers_server_list')

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(ServerCreate, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        return_value = super(ServerCreate, self).form_valid(form)
        event_handlers.on_server_added(self.request, self.object)
        return return_value


class ServerUpdate(UpdateView):
    model = models.Server
    form_class = forms.ServerForm
    success_url = reverse_lazy('servers_server_list')

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(ServerUpdate, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        return_value = super(ServerUpdate, self).form_valid(form)
        event_handlers.on_server_updated(self.request, self.object)
        return return_value


class ServerDelete(DeleteView):
    model = models.Server
    success_url = reverse_lazy('servers_server_list')

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(ServerDelete, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ServerDelete, self).get_context_data(**kwargs)
        context['form'] = utils_forms.SubmitForm()
        return context

    def delete(self, request, *args, **kwargs):
        to_be_deleted_object = self.get_object()
        return_value = super(ServerDelete, self).delete(
            request, *args, **kwargs)
        event_handlers.on_server_deleted(self.request, to_be_deleted_object)
        return return_value


class DiscoverMySqlServers(TemplateView):
    template_name = 'servers/discover_mysql_servers.html'

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(DiscoverMySqlServers, self).dispatch(
            request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DiscoverMySqlServers, self).get_context_data(**kwargs)
        context['mysql_servers'] = server_discovery.discover_mysql_servers(
            settings.NMAP_HOSTS, settings.NMAP_PORTS)
        return context

    def post(self, request, *args, **kwargs):
        for k, v in request.POST.iteritems():
            if k.startswith('server_'):
                name, hostname, port = v.split(',')
                servers = models.Server.objects.filter(
                    hostname=hostname, port=port)
                if not servers.exists():
                    server = models.Server.objects.create(
                        name=name, hostname=hostname, port=port)
                    event_handlers.on_server_added(request, server)
        return redirect('servers_server_list')


class ServerDataList(ListView):
    model = models.ServerData

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(ServerDataList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        qs = models.ServerData.objects.all()
        database_schema_id = self.request.GET.get('database_schema_id')
        if database_schema_id:
            qs = qs.filter(database_schema__id=int(database_schema_id))
        return qs


class ServerData(DetailView):
    model = models.ServerData

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(ServerData, self).dispatch(
            request, *args, **kwargs)
