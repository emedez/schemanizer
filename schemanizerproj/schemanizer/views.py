import cStringIO as StringIO
import json
import logging
from pprint import pformat
import urllib

#warnings.filterwarnings('ignore', category=MySQLdb.Warning)

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.servers.basehttp import FileWrapper
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http import HttpResponseForbidden, HttpResponse, Http404
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string

from celery import states
from celery.result import AsyncResult
from djcelery import humanize as djcelery_humanize
import djcelery.models as djcelery_models
import yaml

from schemanizer import exceptions, forms, models, utilities
from schemanizer.logic import changeset_logic
from schemanizer.logic import changeset_apply_logic
from schemanizer.logic import changeset_review_logic
from schemanizer.logic import privileges_logic
from schemanizer.logic import user_logic
from schemaversions.models import DatabaseSchema, SchemaVersion
from servers.forms import ServerForm
from servers.models import Environment, Server
from servers.server_discovery import discover_mysql_servers
from users.forms import UserAddForm, UserUpdateForm
from users.models import Role, User
from users.user_functions import add_user, update_user
from utils.exceptions import Error

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
            changesets = models.Changeset.objects.get_needs_review()
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_soft_delete(
        request, id, template='schemanizer/changeset_soft_delete.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        changeset = models.Changeset.objects.get(pk=int(id))
        user_has_access = (
            privileges_logic.UserPrivileges(user)
            .can_soft_delete_changeset(changeset))
        if user_has_access:
            if request.method == 'POST':
                changeset_logic.soft_delete_changeset(changeset, user)
                messages.success(
                    request, 'Changeset [id=%s] was soft deleted.' % (id,))
                return redirect('schemanizer_changeset_list')
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_submit(request, template='schemanizer/changeset_update.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in Role.ROLE_LIST
        if user_has_access:
            changeset = models.Changeset()
            ChangesetDetailFormSet = inlineformset_factory(
                models.Changeset, models.ChangesetDetail,
                form=forms.ChangesetDetailForm,
                extra=1, can_delete=False)
            if request.method == 'POST':
                changeset_form = forms.ChangesetForm(
                    request.POST, instance=changeset)
                changeset_detail_formset = ChangesetDetailFormSet(
                    request.POST, instance=changeset)
                if (changeset_form.is_valid() and
                        changeset_detail_formset.is_valid()):
                    changeset = (
                        changeset_logic.process_changeset_form_submission(
                            changeset_form=changeset_form,
                            changeset_detail_formset=changeset_detail_formset,
                            user=user))
                    messages.success(
                        request,
                        u'Changeset [id=%s] was submitted, '
                        u'review procedure has been started, '
                        u'when completed, an email will be sent to '
                        u'interested parties.' % (
                            changeset.id,))
                    return redirect(
                        'schemanizer_changeset_reviews')
            else:
                changeset_form = forms.ChangesetForm(instance=changeset)
                changeset_detail_formset = ChangesetDetailFormSet(instance=changeset)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_update(request, id, template='schemanizer/changeset_update.html'):
    """Update changeset page."""

    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            Role.ROLE_DEVELOPER,
            Role.ROLE_DBA,
            Role.ROLE_ADMIN)

        if user_has_access:
            changeset = models.Changeset.objects.get(pk=int(id))
            if privileges_logic.UserPrivileges(user).can_update_changeset(
                    changeset):
                ChangesetDetailFormSet = inlineformset_factory(
                    models.Changeset, models.ChangesetDetail,
                    form=forms.ChangesetDetailForm,
                    extra=1, can_delete=True)
                if request.method == 'POST':
                    changeset_form = forms.ChangesetForm(
                        request.POST, instance=changeset)
                    changeset_detail_formset = ChangesetDetailFormSet(
                        request.POST, instance=changeset)
                    if changeset_form.is_valid() and changeset_detail_formset.is_valid():
                        with transaction.commit_on_success():
                            changeset = changeset_logic.changeset_update_from_form(
                                changeset_form=changeset_form,
                                changeset_detail_formset=changeset_detail_formset,
                                user=user)
                        messages.success(
                            request, u'Changeset [id=%s] was updated.' % (
                                changeset.id,))
                        return redirect(
                            'schemanizer_changeset_view', changeset.id)
                else:
                    changeset_form = forms.ChangesetForm(instance=changeset)
                    changeset_detail_formset = ChangesetDetailFormSet(
                        instance=changeset)
            else:
                messages.error(request, MSG_USER_NO_ACCESS)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_view_review_results(
        request, changeset_id,
        template='schemanizer/changeset_view_review_results.html'):
    user_has_access = False

    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            Role.ROLE_DEVELOPER,
            Role.ROLE_DBA,
            Role.ROLE_ADMIN)
        if user_has_access:
            changeset = models.Changeset.objects.get(pk=int(changeset_id))
            changeset_review = None
            try:
                changeset_review = models.ChangesetReview.objects.get(
                    changeset=changeset)
            except ObjectDoesNotExist:
                pass
            if (
                    changeset.review_status in [
                        models.Changeset.REVIEW_STATUS_IN_PROGRESS,
                        models.Changeset.REVIEW_STATUS_APPROVED]
                    ):
                changeset_review_success = True
            if (
                    changeset.review_status ==
                        models.Changeset.REVIEW_STATUS_REJECTED
                    ):
                changeset_review_failed = True
            changeset_validations = models.ChangesetValidation.objects.filter(
                changeset=changeset).order_by('id')
            changeset_validation_ids = request.GET.get(
                'changeset_validation_ids', None)
            if changeset_validation_ids:
                changeset_validation_ids = [
                    int(id) for id in changeset_validation_ids.split(',')]
                changeset_validations = changeset_validations.filter(
                    id__in=changeset_validation_ids)
            changeset_tests = models.ChangesetTest.objects.filter(
                changeset_detail__changeset=changeset).order_by('id')
            changeset_test_ids = request.GET.get('changeset_test_ids', None)
            if changeset_test_ids:
                changeset_test_ids = [
                    int(id) for id in changeset_test_ids.split(',')]
                changeset_tests = changeset_tests.filter(
                    id__in=changeset_test_ids)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_view(request, id, template='schemanizer/changeset_view.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            Role.ROLE_DEVELOPER,
            Role.ROLE_DBA,
            Role.ROLE_ADMIN)

        if user_has_access:
            id = int(id)
            changeset = models.Changeset.objects.select_related().get(id=id)

            changeset_applies = models.ChangesetApply.objects.filter(
                changeset=changeset)

            changeset_action_qs = models.ChangesetAction.objects.filter(
                changeset=changeset)
            changeset_actions = []
            for changeset_action in changeset_action_qs:
                changeset_action_server_map_qs = (
                    models.ChangesetActionServerMap.objects.filter(
                        changeset_action=changeset_action))
                changeset_action_server_map = None
                if changeset_action_server_map_qs.exists():
                    changeset_action_server_map = (
                        changeset_action_server_map_qs[0])
                type_col = changeset_action.type

                changeset_applies_url = None
                changeset_apply_qs = models.ChangesetApply.objects.filter(
                    changeset_action=changeset_action)
                if changeset_apply_qs.exists():
                    changeset_apply = changeset_apply_qs[0]
                    if changeset_apply.task_id:
                        changeset_applies_url = '%s?%s' % (
                            reverse('schemanizer_changeset_applies'),
                            urllib.urlencode(
                                dict(task_id=changeset_apply.task_id)))

                if (
                        type_col == models.ChangesetAction.TYPE_APPLIED and
                        changeset_action_server_map):
                    server = changeset_action_server_map.server
                    server_name = server.name
                    environment_name = None
                    if server.environment:
                        environment_name = server.environment.name
                    type_col = (
                        u'%s (server: %s, environment: %s)' % (
                            type_col, server_name, environment_name))
                elif(
                        type_col == models.ChangesetAction.TYPE_APPLIED_FAILED and
                        changeset_action_server_map):
                    server = changeset_action_server_map.server
                    server_name = server.name
                    environment_name = None
                    if server.environment:
                        environment_name = server.environment.name
                    type_col = (
                        u'%s (server: %s, environment: %s)' % (
                            type_col, server_name, environment_name))


                changeset_actions.append(
                    dict(
                        changeset_action=changeset_action,
                        changeset_action_server_map=
                        changeset_action_server_map,
                        type=type_col,
                        changeset_applies_url=changeset_applies_url))

            if request.method == 'POST':
                try:
                    if u'submit_update' in request.POST:
                        #
                        # Update changeset
                        #
                        return redirect(
                            'schemanizer_changeset_update', changeset.id)

                    elif u'submit_review' in request.POST:
                        #
                        # Set changeset review status to 'in_progress'
                        #
                        return redirect(
                            'schemanizer_changeset_review',
                            changeset.id)

                    elif u'submit_approve' in request.POST:
                        #
                        # Approve changeset.
                        #
                        with transaction.commit_on_success():
                            changeset_logic.changeset_approve(
                                changeset=changeset, user=user)
                        messages.success(
                            request, u'Changeset [id=%s] was approved.' % (
                                changeset.id,))

                    elif u'submit_reject' in request.POST:
                        #
                        # Reject changeset.
                        #
                        with transaction.commit_on_success():
                            changeset_logic.changeset_reject(
                                changeset=changeset, user=user)
                        messages.success(
                            request, u'Changeset [id=%s] was rejected.' % (
                                changeset.id,))

                    elif u'submit_delete' in request.POST:
                        #
                        # Delete changeset.
                        #
                        return redirect(reverse(
                            'schemanizer_changeset_soft_delete',
                            args=[changeset.id]))

                    elif u'submit_apply' in request.POST:
                        #
                        # Apply changeset
                        #
                        return redirect(
                            'schemanizer_changeset_apply', changeset.id)

                    else:
                        messages.error(request, u'Unknown command.')
                        log.error(
                            u'Invalid post.\nrequest.POST=\n%s' % (
                                pformat(request.POST),))

                except exceptions.PrivilegeError, e:
                    log.exception('EXCEPTION')
                    messages.error(request, u'%s' % (e,))

            user_privileges = privileges_logic.UserPrivileges(user)
            can_update = user_privileges.can_update_changeset(changeset)
            can_set_review_status_to_in_progress = (
                privileges_logic.can_user_review_changeset(user, changeset))
            can_approve = user_privileges.can_approve_changeset(changeset)
            can_reject = user_privileges.can_reject_changeset(changeset)
            can_soft_delete = (
                privileges_logic.UserPrivileges(user)
                .can_soft_delete_changeset(changeset))
            can_apply = privileges_logic.can_user_apply_changeset(
                user, changeset)

            if (
                    changeset.review_status in [
                        models.Changeset.REVIEW_STATUS_IN_PROGRESS,
                        models.Changeset.REVIEW_STATUS_APPROVED,
                        models.Changeset.REVIEW_STATUS_REJECTED]
                    ):
                show_changeset_detail_test_status = True

        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_list(request, template='schemanizer/changeset_list.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            Role.ROLE_DEVELOPER, Role.ROLE_DBA,
            Role.ROLE_ADMIN)
        if user_has_access:
            qs = models.Changeset.objects.get_not_deleted()
            changesets = []
            for r in qs:
                extra=dict(
                    can_apply=privileges_logic.can_user_apply_changeset(
                        user, r),
                    can_review=
                        privileges_logic.can_user_review_changeset(user, r))
                changesets.append(dict(r=r, extra=extra))
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
        can_soft_delete = user.role.name in (Role.ROLE_ADMIN,)
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
            changeset = models.Changeset.objects.get(pk=int(changeset_id))

            if not privileges_logic.can_user_apply_changeset(user, changeset):
                raise exceptions.PrivilegeError(
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


@login_required
def changeset_apply(
        request, changeset_id, template='schemanizer/changeset_apply.html'):
    """View for applying changeset."""

    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            Role.ROLE_DEVELOPER,
            Role.ROLE_DBA,
            Role.ROLE_ADMIN)
        if user_has_access:
            request_id = utilities.generate_request_id(request)
            changeset = models.Changeset.objects.get(pk=int(changeset_id))

            environments = Environment.objects.all()

            if not privileges_logic.can_user_apply_changeset(user, changeset):
                raise exceptions.PrivilegeError(
                    'User is not allowed to apply changeset.')

            # if request.method == 'POST':
            #     form = forms.SelectServerForm(request.POST)
            #     show_form = True
            #     if form.is_valid():
            #         server = models.Server.objects.get(pk=int(
            #             form.cleaned_data['server']))
            #         thread = changeset_apply_logic.start_changeset_apply_thread(
            #             changeset, user, server)
            #         apply_threads[request_id] = thread
            #         poll_thread_status = True
            #         show_form = False
            # else:
            #     form = forms.SelectServerForm()
            #     show_form = True

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


@login_required
def changeset_review(
        request, changeset_id,
        template='schemanizer/changeset_review.html'):
    from schemanizer import tasks

    user_has_access = False
    try:
        request_id = utilities.generate_request_id(request)
        changeset = models.Changeset.objects.get(pk=int(changeset_id))
        user = request.user.schemanizer_user
        user_has_access = privileges_logic.can_user_review_changeset(
            user, changeset)
        schema_version = request.GET.get('schema_version', None)
        if schema_version:
            schema_version = SchemaVersion.objects.get(
                pk=int(schema_version))

        if user_has_access:
            if request.method == 'POST':

                if u'select_schema_version_form_submit' in request.POST:
                    #
                    # process select schema version form submission
                    #
                    select_schema_version_form = (
                        forms.SelectSchemaVersionForm(
                            request.POST,
                            database_schema=changeset.database_schema))
                    if select_schema_version_form.is_valid():
                        schema_version = int(
                            select_schema_version_form.cleaned_data[
                                'schema_version'])
                        # url = reverse(
                        #     'schemanizer_changeset_review',
                        #     args=[changeset.id])
                        # query_string = urllib.urlencode(
                        #     dict(schema_version=schema_version))
                        # #
                        # # redirect to actual changeset syntax validation procedure
                        # return redirect('%s?%s' % (url, query_string))

                        tasks.review_changeset.delay(
                            changeset=changeset.pk,
                            schema_version=schema_version,
                            user=user.pk)
                        messages.info(
                            request,
                            u'Changeset review has been started, email will '
                            u'be sent to interested parties when review '
                            u'procedure is completed.')

                        return redirect('schemanizer_changeset_reviews')

                else:
                    #
                    # Invalid POST.
                    #
                    messages.error(request, u'Unknown command.')

            else:
                #
                # GET
                #

                if schema_version:
                    #
                    # User has selected a schema version already,
                    # proceed with changeset review.
                    #
                    thread = changeset_review_logic.start_changeset_review_thread(
                        changeset, schema_version, user)
                    review_threads[request_id] = thread
                    thread_started = True

                else:
                    #
                    # No schema version was selected yet,
                    # ask one from user
                    #
                    select_schema_version_form = forms.SelectSchemaVersionForm(
                        database_schema=changeset.database_schema)

        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))

    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


def select_environment_servers(
        request, template='schemanizer/select_environment_servers.html'):
    """Ajax view for selecting environment servers."""

    if not request.is_ajax():
        return HttpResponseForbidden(MSG_NOT_AJAX)

    data = {}
    try:
        if not request.user.is_authenticated():
            raise Error('Login is required.')

        environment_id = request.GET['environment_id'].strip()
        changeset_id = request.GET['changeset_id'].strip()

        if environment_id:
            environment_id = int(environment_id)
            environment = Environment.objects.get(pk=environment_id)
            servers = Server.objects.filter(environment=environment)
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


def ajax_get_schema_version(
        request, template='schemanizer/ajax_get_schema_version.html'):
    if not request.is_ajax():
        return HttpResponseForbidden(MSG_NOT_AJAX)

    data = {}
    try:
        if not request.user.is_authenticated():
            raise Exception('Login is required.')

        schema_version_id = request.GET['schema_version_id'].strip()
        if schema_version_id:
            schema_version_id = int(schema_version_id)
            schema_version = SchemaVersion.objects.get(
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


def ajax_changeset_applies(
        request, template='schemanizer/ajax_changeset_applies.html'):
    """Ajax view for changeset applies."""

    if not request.is_ajax():
        return HttpResponseForbidden(MSG_NOT_AJAX)

    data = {}
    try:
        if not request.user.is_authenticated():
            raise Error('Login is required.')

        request_id = request.GET.get('request_id')
        task_id = request.GET.get('task_id')
        task_ids = None
        if task_id:
            task_ids = [task_id]
        else:
            if request_id and request_id in request.session:
                task_ids = request.session[request_id]
        filter_kwargs = dict(name='schemanizer.tasks.apply_changeset')
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
                    server = Server.objects.get(pk=server_id)
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


@login_required
def changeset_applies(request, template='schemanizer/changeset_applies.html'):
    """View for displaying statuses of changeset applies."""

    request_id = request.GET.get('request_id')
    task_id = request.GET.get('task_id')

    get_params = {}
    if request_id:
        get_params['request_id'] = request_id
    if task_id:
        get_params['task_id'] = task_id
    ajax_changeset_applies_url = '%s?%s' % (
        reverse('schemanizer_ajax_changeset_applies'),
        urllib.urlencode(get_params))

    # task_ids = None
    # if task_id:
    #     task_ids = [task_id]
    # else:
    #     if request_id and request_id in request.session:
    #         task_ids = request.session[request_id]
    # filter_kwargs = dict(name='schemanizer.tasks.apply_changeset')
    # if task_ids:
    #     filter_kwargs.update(dict(task_id__in=task_ids))
    # task_states = djcelery_models.TaskState.objects.filter(
    #     **filter_kwargs)
    # task_state_list = []
    # for task_state in task_states:
    #     ar = AsyncResult(task_state.task_id)
    #     result = ar.result
    #
    #     if result and isinstance(result, dict) and 'message' in result:
    #         show_message = True
    #     else:
    #         show_message = False
    #
    #     changeset_id = None
    #     server = None
    #     changeset_detail_applies = []
    #     if result:
    #         changeset_id = result.get('changeset_id')
    #         server_id = result.get('server_id')
    #         changeset_detail_apply_ids = result.get(
    #             'changeset_detail_apply_ids')
    #         log.debug('changeset_detail_apply_ids = %s', changeset_detail_apply_ids)
    #         if server_id:
    #             server = models.Server.objects.get(pk=server_id)
    #         if changeset_detail_apply_ids:
    #             for id in changeset_detail_apply_ids:
    #                 changeset_detail_applies.append(
    #                     models.ChangesetDetailApply.objects.get(pk=id))
    #             log.debug(changeset_detail_applies)
    #
    #     task_state_list.append(dict(
    #         task_id=task_state.task_id,
    #         tstamp=djcelery_humanize.naturaldate(task_state.tstamp),
    #         state=task_state.state,
    #         result=result,
    #         show_message=show_message,
    #         changeset_id=changeset_id,
    #         server=server,
    #         changeset_detail_applies=changeset_detail_applies
    #     ))

    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


def ajax_changeset_reviews(
        request, template='schemanizer/ajax_changeset_reviews.html'):
    """Ajax view for on-going changeset review jobs."""

    if not request.is_ajax():
        return HttpResponseForbidden(MSG_NOT_AJAX)

    data = {}
    try:
        if not request.user.is_authenticated():
            raise Error('Login is required.')

        task_states = djcelery_models.TaskState.objects.filter(
            name='schemanizer.tasks.review_changeset',
            state__in=states.UNREADY_STATES)
        task_state_list = []
        for task_state in task_states:
            ar = AsyncResult(task_state.task_id)
            result = ar.result
            if result and isinstance(result, dict) and 'message' in result:
                show_message = True
            else:
                show_message = False
            kwargs_obj = {}
            if task_state.kwargs:
                try:
                    kwargs_obj = yaml.load(task_state.kwargs)
                    if 'changeset' in kwargs_obj:
                        kwargs_obj['changeset'] = long(kwargs_obj['changeset'])
                except:
                    pass
            changeset_id = kwargs_obj.get('changeset')
            show_changeset_view_url = False
            if changeset_id:
                show_changeset_view_url = (
                    models.Changeset.objects.filter(pk=changeset_id).exists())

            task_state_list.append(dict(
                task_id=task_state.task_id,
                tstamp=djcelery_humanize.naturaldate(task_state.tstamp),
                state=task_state.state,
                params=task_state.kwargs,
                #result=task_state.result,
                result=result,
                show_message=show_message,
                changeset_id=changeset_id,
                show_changeset_view_url=show_changeset_view_url,
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


@login_required
def changeset_reviews(
        request, template='schemanizer/changeset_reviews.html'):
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def apply_changeset_to_multiple_hosts(
        request, changeset_id,
        template='schemanizer/apply_changeset_to_multiple_hosts.html'):
    """Apply changeset POST handler."""

    from schemanizer import tasks

    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            Role.ROLE_DEVELOPER,
            Role.ROLE_DBA,
            Role.ROLE_ADMIN)
        if user_has_access:
            request_id = utilities.generate_request_id(request)
            changeset = models.Changeset.objects.get(pk=int(changeset_id))

            if not privileges_logic.can_user_apply_changeset(user, changeset):
                raise exceptions.PrivilegeError(
                    'User is not allowed to apply changeset.')

            if (
                    changeset.review_status !=
                    models.Changeset.REVIEW_STATUS_APPROVED):
                raise Error('Cannot apply unapproved changeset.')

            if request.method == 'POST':
                log.debug(request.POST)

                server_ids = []
                for k, v in request.POST.iteritems():
                    if k.startswith('server_'):
                        server_ids.append(int(v))

                task_ids = []
                for server_id in server_ids:
                    result = tasks.apply_changeset.delay(
                        changeset.id, user.id, server_id)
                    task_ids.append(result.task_id)

                request_id = utilities.generate_request_id(request)
                request.session[request_id] = task_ids

                redirect_url = reverse('schemanizer_changeset_applies')
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

