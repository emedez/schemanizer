import codecs
import json
import logging
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
import markdown
from changesets.models import Changeset
from schemanizer import forms, utilities
from schemanizer.logic import changeset_apply_logic
from schemanizer.logic import privileges_logic
from schemaversions.models import DatabaseSchema, SchemaVersion
from servers.forms import ServerForm
from servers.models import Environment, Server
from servers.server_discovery import discover_mysql_servers
from users.models import Role
from utils.exceptions import PrivilegeError

log = logging.getLogger(__name__)

MSG_USER_NO_ACCESS = u'You do not have access to this page.'
MSG_NOT_AJAX = u'Request must be a valid XMLHttpRequest.'

review_threads = {}
apply_threads = {}


@login_required
def home(request, template='schemanizer/home.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in Role.ROLE_LIST
        if user.role.name in (Role.ROLE_DBA, Role.ROLE_ADMIN):
            show_to_be_reviewed_changesets = True
            can_apply_changesets = True
            changesets = Changeset.to_be_reviewed_objects.all()
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


def readme(request, template='schemanizer/readme.html'):
    user_has_access = False
    try:
        readme_path = os.path.abspath(
            os.path.join(settings.PROJECT_ROOT, '..', 'README.md'))
        input_file = codecs.open(readme_path, mode="r", encoding="utf-8")
        text = input_file.read()
        html = markdown.markdown(text)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))

















@login_required
def changeset_apply_old(
        request, changeset_id, template='schemanizer/changeset_apply.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            Role.ROLE_DEVELOPER,
            Role.ROLE_DBA,
            Role.ROLE_ADMIN)
        if user_has_access:
            request_id = utilities.generate_request_id(request)
            changeset = Changeset.objects.get(pk=int(changeset_id))

            if not privileges_logic.can_user_apply_changeset(user, changeset):
                raise PrivilegeError(
                    'User is not allowed to apply changeset.')

            if request.method == 'POST':
                form = forms.SelectServerForm(request.POST)
                show_form = True
                if form.is_valid():
                    server = Server.objects.get(pk=int(
                        form.cleaned_data['server']))
                    thread = changeset_apply_logic.start_changeset_apply_thread(
                        changeset, user, server)
                    apply_threads[request_id] = thread
                    poll_thread_status = True
                    show_form = False
            else:
                form = forms.SelectServerForm()
                show_form = True

        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))





def changeset_apply_status(
        request, request_id,
        template='schemanizer/changeset_apply_status.html',
        changeset_detail_applies_template=
            'schemanizer/changeset_apply_changeset_detail_applies.html'):

    if not request.is_ajax():
        return HttpResponseForbidden(MSG_NOT_AJAX)

    data = {}
    try:
        if not request.user.is_authenticated():
            raise Exception('Login is required.')

        t = apply_threads.get(request_id, None)
        if not t:
            #
            # There was no running thread associated with the request_id,
            # It is either request ID is invalid or thread had completed
            # already and was removed from the dictionary.
            #
            data['error'] = u'Invalid request ID.'

        else:
            t_is_alive = t.is_alive()
            data['thread_is_alive'] = t_is_alive
            data['thread_messages_html'] = render_to_string(
                template,
                {
                    'messages': t.messages
                },
                context_instance=RequestContext(request))

            if not t_is_alive:
                #
                # Remove dead threads from dictionary.
                #
                apply_threads.pop(request_id, None)

                data['thread_has_errors'] = t.has_errors
                data['thread_changeset_detail_applies_html'] = render_to_string(
                    changeset_detail_applies_template,
                    dict(
                        changeset=t.changeset,
                        changeset_detail_applies=t.changeset_detail_applies
                    ),
                    context_instance=RequestContext(request)
                )

        data_json = json.dumps(data)
    except Exception, e:
        log.exception('EXCEPTION')
        data = dict(error=u'%s' % (e,))
        data_json = json.dumps(data)

    return HttpResponse(data_json, mimetype='application/json')











def changeset_review_status(
        request, request_id,
        messages_template='schemanizer/changeset_review_status_messages.html'):

    if not request.is_ajax():
        return HttpResponseForbidden(MSG_NOT_AJAX)

    data = {}
    try:
        if not request.user.is_authenticated():
            raise Exception('Login is required.')

        t = review_threads.get(request_id, None)
        if not t:
            #
            # There was no running thread associated with the request_id,
            # It is either request ID is invalid or thread had completed
            # already and was removed from the dictionary.
            #
            data['error'] = u'Invalid request ID.'

        else:
            t_is_alive = t.is_alive()
            data['thread_is_alive'] = t_is_alive
            data['thread_errors'] = t.errors
            if t.messages:
                data['thread_messages'] = t.messages[-1:]
            else:
                data['thread_messages'] = []
            data['thread_messages_html'] = render_to_string(
                messages_template, {'thread_messages': data['thread_messages']},
                context_instance=RequestContext(request))

            if not t_is_alive:
                #
                # Remove dead threads from dictionary.
                #
                review_threads.pop(request_id, None)
                if t.review_results_url:
                    data['thread_review_results_url'] = t.review_results_url

        data_json = json.dumps(data)
    except Exception, e:
        log.exception('EXCEPTION')
        data = dict(error=u'%s' % (e,))
        data_json = json.dumps(data)

    return HttpResponse(data_json, mimetype='application/json')


@login_required
def server_list(request, template='schemanizer/server_list.html'):
    """Server list view."""
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        role_name = user.role.name
        user_has_access = (
            role_name in [
                Role.ROLE_DEVELOPER,
                Role.ROLE_DBA,
                Role.ROLE_ADMIN])

        if user_has_access:
            servers = Server.objects.all()

        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def server_update(request, id=None, template='schemanizer/server_update.html'):
    """Server update view."""
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        role_name = user.role.name
        user_has_access = (
            role_name in [
                Role.ROLE_DEVELOPER,
                Role.ROLE_DBA,
                Role.ROLE_ADMIN])

        if user_has_access:
            if id:
                server = Server.objects.get(pk=int(id))
            else:
                server = Server()
            if request.method == 'POST':
                form = ServerForm(request.POST, instance=server)
                if form.is_valid():
                    server = form.save()
                    msg = u'Server [id=%s] was %s.' % (
                        server.id, u'updated' if id else u'created')
                    messages.success(request, msg)
                    log.info(msg)
                    return redirect('schemanizer_server_list')
            else:
                form = ServerForm(instance=server)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def server_delete(request, id, template='schemanizer/server_delete.html'):
    """Server delete view."""

    user_has_access = False
    try:
        user = request.user.schemanizer_user
        role_name = user.role.name
        user_has_access = (
            role_name in [
                Role.ROLE_DEVELOPER,
                Role.ROLE_DBA,
                Role.ROLE_ADMIN])

        if user_has_access:
            server = Server.objects.get(pk=int(id))
            if request.method == 'POST':
                with transaction.commit_on_success():
                    server.delete()
                msg = u'Server [id=%s] was deleted.' % (id,)
                messages.success(request, msg)
                log.info(msg)
                return redirect('schemanizer_server_list')
            else:
                form = forms.ContinueForm()

        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def database_schema_list(
        request, template='schemanizer/database_schema_list.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        role_name = user.role.name
        user_has_access = (
            role_name in [
                Role.ROLE_DEVELOPER,
                Role.ROLE_DBA,
                Role.ROLE_ADMIN])

        if user_has_access:
            database_schemas = DatabaseSchema.objects.all()
        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def schema_version_list(
        request, template='schemanizer/schema_version_list.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        role_name = user.role.name
        user_has_access = (
            role_name in [
                Role.ROLE_DEVELOPER,
                Role.ROLE_DBA,
                Role.ROLE_ADMIN])

        database_schema = request.GET.get('database_schema', None)

        if user_has_access:
            schema_versions = SchemaVersion.objects.all()
            if database_schema:
                schema_versions = schema_versions.filter(
                    database_schema_id=int(database_schema))
        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def schema_version_view(
        request, schema_version_id,
        template='schemanizer/schema_version_view.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        role_name = user.role.name
        user_has_access = (
            role_name in [
                Role.ROLE_DEVELOPER,
                Role.ROLE_DBA,
                Role.ROLE_ADMIN])

        if user_has_access:
            r = SchemaVersion.objects.get(pk=int(schema_version_id))
        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def environment_list(request, template='schemanizer/environment_list.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        role_name = user.role.name
        user_has_access = (
            role_name in [
                Role.ROLE_DEVELOPER,
                Role.ROLE_DBA,
                Role.ROLE_ADMIN])

        if user_has_access:
            qs = Environment.objects.all()
            can_add = can_update = can_delete = role_name in [
                Role.ROLE_DBA, Role.ROLE_ADMIN]
        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def environment_update(
        request, environment_id=None,
        template='schemanizer/environment_update.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        role_name = user.role.name
        user_has_access = (
            role_name in [
                Role.ROLE_DBA,
                Role.ROLE_ADMIN])

        if user_has_access:
            if environment_id:
                r = Environment.objects.get(pk=int(environment_id))
            else:
                r = Environment()
            if request.method == 'POST':
                form = forms.EnvironmentForm(request.POST, instance=r)
                if form.is_valid():
                    r = form.save()
                    if environment_id:
                        messages.success(
                            request,
                            u'Environment [ID=%s] was updated.' % (r.id,))
                    else:
                        messages.success(
                            request,
                            u'Environment [ID=%s] was created.' % (r.id,))
                    return redirect('schemanizer_environment_list')
            else:
                form = forms.EnvironmentForm(instance=r)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def environment_del(
        request, environment_id=None,
        template='schemanizer/environment_del.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        role_name = user.role.name
        user_has_access = (
            role_name in [
                Role.ROLE_DBA,
                Role.ROLE_ADMIN])

        if user_has_access:
            r = Environment.objects.get(pk=int(environment_id))
            if request.method == 'POST':
                r.delete()
                messages.success(
                    request,
                    u'Environment [ID=%s] was deleted.' % (environment_id,))
                return redirect('schemanizer_environment_list')
        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def server_discover(request, template='schemanizer/server_discover.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            Role.ROLE_DEVELOPER, Role.ROLE_DBA,
            Role.ROLE_ADMIN)
        if user_has_access:
            if request.method == 'POST':
                for k, v in request.POST.iteritems():
                    if k.startswith('server_'):
                        name, hostname, port = v.split(',')
                        with transaction.commit_on_success():
                            qs = Server.objects.filter(
                                hostname=hostname, port=port)
                            if not qs.exists():
                                Server.objects.create(
                                    name=name, hostname=hostname, port=port)
                                messages.info(
                                    request,
                                    u'Server %s was added.' % (hostname,))
                return redirect('schemanizer_server_list')
            else:
                mysql_servers = discover_mysql_servers(
                    settings.NMAP_HOSTS, settings.NMAP_PORTS)

        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))
















