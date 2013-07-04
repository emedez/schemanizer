import json
import logging
import urllib
from celery.result import AsyncResult
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from djcelery import models as djcelery_models, humanize as djcelery_humanize
from changesets import models as changesets_models
from servers import models as servers_models
from users import models as users_models
from utils import exceptions, helpers
from . import tasks, models
from schemanizer.logic import privileges_logic

log = logging.getLogger(__name__)
MSG_USER_NO_ACCESS = u'You do not have access to this page.'
MSG_NOT_AJAX = u'Request must be a valid XMLHttpRequest.'


@login_required
def changeset_apply(request, changeset_pk,
                    template='changesetapplies/changeset_apply.html'):
    """View for applying changeset."""

    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            users_models.Role.NAME.developer,
            users_models.Role.NAME.dba,
            users_models.Role.NAME.admin)
        if user_has_access:
            request_id = helpers.generate_request_id(request)
            changeset = changesets_models.Changeset.objects.get(pk=int(changeset_pk))

            environments = servers_models.Environment.objects.all()

            if not privileges_logic.can_user_apply_changeset(user, changeset):
                raise exceptions.PrivilegeError(
                    'User is not allowed to apply changeset.')

        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))

    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


def select_environment_servers(
        request, template='changesetapplies/select_environment_servers.html'):
    """Ajax view for selecting environment servers."""

    if not request.is_ajax():
        return HttpResponseForbidden(MSG_NOT_AJAX)

    data = {}
    try:
        if not request.user.is_authenticated():
            raise exceptions.Error('Login is required.')

        environment_id = request.GET['environment_id'].strip()
        changeset_id = request.GET['changeset_id'].strip()

        if environment_id:
            environment_id = int(environment_id)
            environment = servers_models.Environment.objects.get(pk=environment_id)
            servers = servers_models.Server.objects.filter(environment=environment)
            data['html'] = render_to_string(
                template, locals(), context_instance=RequestContext(request))
        else:
            data['html'] = ''

        data_json = json.dumps(data)

    except Exception, e:
        msg = 'ERROR %s: %s' % (type(e), e)
        log.exception(msg)
        data = dict(error=msg, html='')
        data_json = json.dumps(data)

    return HttpResponse(data_json, mimetype='application/json')


@login_required
def apply_changeset_to_multiple_hosts(request, changeset_pk,
                                      template='changesetapplies/apply_changeset_to_multiple_hosts.html'):
    """Apply changeset POST handler."""

    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            users_models.Role.NAME.developer,
            users_models.Role.NAME.dba,
            users_models.Role.NAME.admin)
        if user_has_access:
            request_id = helpers.generate_request_id(request)
            changeset = changesets_models.Changeset.objects.get(pk=int(changeset_pk))

            if not privileges_logic.can_user_apply_changeset(user, changeset):
                raise exceptions.PrivilegeError(
                    'User is not allowed to apply changeset.')

            if (
                    changeset.review_status !=
                    changesets_models.Changeset.REVIEW_STATUS_APPROVED):
                raise exceptions.Error('Cannot apply unapproved changeset.')

            if request.method == 'POST':
                log.debug(request.POST)

                server_ids = []
                for k, v in request.POST.iteritems():
                    if k.startswith('server_'):
                        server_ids.append(int(v))

                if not server_ids:
                    raise exceptions.Error('No server was selected.')

                if not changeset.before_version and len(server_ids) > 1:
                    raise exceptions.Error(
                        'This changeset is going to be applied for the '
                        'first time, select a single server only.')

                task_ids = []
                for server_id in server_ids:
                    result = tasks.apply_changeset.delay(
                        changeset.id, user.id, server_id)
                    task_ids.append(result.task_id)

                request_id = helpers.generate_request_id(request)
                request.session[request_id] = task_ids

                redirect_url = reverse('changesetapplies_changeset_applies')
                redirect_url = '%s?request_id=%s' % (redirect_url, request_id)
                messages.info(request, 'Added new changeset apply task(s).')
                return redirect(redirect_url)

        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))

    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_applies(request, template='changesetapplies/changeset_applies.html'):
    """View for displaying statuses of changeset applies."""

    request_id = request.GET.get('request_id')
    task_id = request.GET.get('task_id')

    get_params = {}
    if request_id:
        get_params['request_id'] = request_id
    if task_id:
        get_params['task_id'] = task_id
    ajax_changeset_applies_url = '%s?%s' % (
        reverse('changesetapplies_ajax_changeset_applies'),
        urllib.urlencode(get_params))

    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


def ajax_changeset_applies(
        request, template='changesetapplies/ajax_changeset_applies.html'):
    """Ajax view for changeset applies."""

    if not request.is_ajax():
        return HttpResponseForbidden(MSG_NOT_AJAX)

    data = {}
    try:
        if not request.user.is_authenticated():
            raise exceptions.Error('Login is required.')

        request_id = request.GET.get('request_id')
        task_id = request.GET.get('task_id')
        task_ids = None
        if task_id:
            task_ids = [task_id]
        else:
            if request_id and request_id in request.session:
                task_ids = request.session[request_id]
        filter_kwargs = dict(name='changesetapplies.tasks.apply_changeset')
        if task_ids:
            filter_kwargs.update(dict(task_id__in=task_ids))
        task_states = djcelery_models.TaskState.objects.filter(
            **filter_kwargs)
        task_state_list = []
        for task_state in task_states:
            ar = AsyncResult(task_state.task_id)
            result = ar.result

            if result and isinstance(result, dict) and 'message' in result:
                show_message = True
            else:
                show_message = False

            changeset_id = None
            server = None
            changeset_detail_applies = []
            if result:
                changeset_id = result.get('changeset_id')
                server_id = result.get('server_id')
                changeset_detail_apply_ids = result.get(
                    'changeset_detail_apply_ids')
                if server_id:
                    server = servers_models.Server.objects.get(pk=server_id)
                if changeset_detail_apply_ids:
                    for id in changeset_detail_apply_ids:
                        try:
                            changeset_detail_applies.append(
                                models.ChangesetDetailApply.objects.get(pk=id))
                        except:
                            pass

            task_state_list.append(dict(
                task_id=task_state.task_id,
                tstamp=djcelery_humanize.naturaldate(task_state.tstamp),
                state=task_state.state,
                result=result,
                show_message=show_message,
                changeset_id=changeset_id,
                server=server,
                changeset_detail_applies=changeset_detail_applies
            ))

        data['html'] = render_to_string(
            template, locals(), context_instance=RequestContext(request))

        data_json = json.dumps(data)

    except Exception, e:
        msg = 'ERROR %s: %s' % (type(e), e)
        log.exception(msg)
        data = dict(error=msg, html='')
        data_json = json.dumps(data)

    return HttpResponse(data_json, mimetype='application/json')