import json
import logging
from pprint import pformat
import urllib
import warnings

import MySQLdb
#warnings.filterwarnings('ignore', category=MySQLdb.Warning)
import sqlparse

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import timezone

from schemanizer import exceptions, forms, models, utils
from schemanizer.logic import changeset_logic
from schemanizer.logic import changeset_apply_logic
from schemanizer.logic import changeset_review_logic
from schemanizer.logic import privileges_logic
from schemanizer.logic import user_logic

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
        user_has_access = user.role.name in models.Role.ROLE_LIST
        if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
            show_to_be_reviewed_changesets = True
            can_apply_changesets = True
            changesets = models.Changeset.objects.get_needs_review()
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def confirm_delete_user(
        request, id, template='schemanizer/confirm_delete_user.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (models.Role.ROLE_ADMIN,)
        if user_has_access:
            id = int(id)
            to_be_del_user = models.User.objects.get(id=id)
            if request.method == 'POST':
                if 'confirm_delete' in request.POST:
                    user_logic.delete_user(user, to_be_del_user)
                    messages.success(
                        request, 'User was deleted, id=%s.' % (id,))
                    return redirect('schemanizer_users')
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def user_update(request, id, template='schemanizer/update_user.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (models.Role.ROLE_ADMIN,)
        if user_has_access:
            id = int(id)

            # to be updated user
            user2 = models.User.objects.get(id=id)

            initial = dict(
                name=user2.name, email=user2.email, role=user2.role_id)
            if request.method == 'POST':
                form = forms.UpdateUserForm(request.POST, initial=initial)
                if form.is_valid():
                    name = form.cleaned_data['name']
                    email = form.cleaned_data['email']
                    role_id = form.cleaned_data['role']
                    role = models.Role.objects.get(id=role_id)
                    schemanizer_user = user_logic.update_user(
                        user, id, name, email, role)
                    messages.success(
                        request, u'User was updated, id=%s.' % (
                            schemanizer_user.id,))
                    return redirect('schemanizer_users')
            else:
                form = forms.UpdateUserForm(initial=initial)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def user_create(request, template='schemanizer/user_create.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (models.Role.ROLE_ADMIN,)
        if user_has_access:
            initial = dict(role=1)
            if request.method == 'POST':
                form = forms.CreateUserForm(request.POST, initial=initial)
                if form.is_valid():
                    name = form.cleaned_data['name']
                    email = form.cleaned_data['email']
                    role_id = form.cleaned_data['role']
                    password = form.cleaned_data['password']
                    role = models.Role.objects.get(id=role_id)
                    schemanizer_user = user_logic.create_user(
                        user, name, email, role, password)
                    messages.success(
                        request, u'User was created, id=%s.' % (
                            schemanizer_user.id,))
                    return redirect('schemanizer_users')
            else:
                form = forms.CreateUserForm(initial=initial)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def users(request, template='schemanizer/users.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (models.Role.ROLE_ADMIN,)
        if user_has_access:
            users = models.User.objects.select_related().all()
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
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
        user_has_access = user.role.name in models.Role.ROLE_LIST
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
                if changeset_form.is_valid() and changeset_detail_formset.is_valid():
                    with transaction.commit_on_success():
                        changeset = changeset_logic.changeset_submit_from_form(
                            changeset_form=changeset_form,
                            changeset_detail_formset=changeset_detail_formset,
                            user=user)
                    messages.success(
                        request, u'Changeset [id=%s] was submitted.' % (
                            changeset.id,))
                    return redirect('schemanizer_changeset_view', changeset.id)
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
            models.Role.ROLE_DEVELOPER,
            models.Role.ROLE_DBA,
            models.Role.ROLE_ADMIN)

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
            models.Role.ROLE_DEVELOPER,
            models.Role.ROLE_DBA,
            models.Role.ROLE_ADMIN)
        if user_has_access:
            changeset = models.Changeset.objects.get(pk=int(changeset_id))
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
            models.Role.ROLE_DEVELOPER,
            models.Role.ROLE_DBA,
            models.Role.ROLE_ADMIN)

        if user_has_access:
            id = int(id)
            changeset = models.Changeset.objects.select_related().get(id=id)
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
            models.Role.ROLE_DEVELOPER, models.Role.ROLE_DBA,
            models.Role.ROLE_ADMIN)
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
        can_soft_delete = user.role.name in (models.Role.ROLE_ADMIN,)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_apply(
        request, changeset_id, template='schemanizer/changeset_apply.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            models.Role.ROLE_DEVELOPER,
            models.Role.ROLE_DBA,
            models.Role.ROLE_ADMIN)
        if user_has_access:
            request_id = utils.generate_request_id(request)
            changeset = models.Changeset.objects.get(pk=int(changeset_id))

            if not privileges_logic.can_user_apply_changeset(user, changeset):
                raise exceptions.PrivilegeError(
                    'User is not allowed to apply changeset.')

            if request.method == 'POST':
                form = forms.SelectServerForm(request.POST)
                show_form = True
                if form.is_valid():
                    server = models.Server.objects.get(pk=int(
                        form.cleaned_data['server']))
                    thread = changeset_apply_logic.changeset_apply(
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


@login_required
def changeset_review(
        request, changeset_id,
        template='schemanizer/changeset_review.html'):

    user_has_access = False
    try:
        request_id = utils.generate_request_id(request)
        changeset = models.Changeset.objects.get(pk=int(changeset_id))
        user = request.user.schemanizer_user
        user_has_access = privileges_logic.can_user_review_changeset(
            user, changeset)
        schema_version = request.GET.get('schema_version', None)
        if schema_version:
            schema_version = models.SchemaVersion.objects.get(
                pk=int(schema_version))

        if user_has_access:
            if request.method == 'POST':

                if u'select_schema_version_form_submit' in request.POST:
                    #
                    # process select schema version form submission
                    #
                    select_schema_version_form = forms.SelectSchemaVersionForm(
                        request.POST, database_schema=changeset.database_schema)
                    if select_schema_version_form.is_valid():
                        schema_version = int(
                            select_schema_version_form.cleaned_data[
                                'schema_version'])
                        url = reverse(
                            'schemanizer_changeset_review',
                            args=[changeset.id])
                        query_string = urllib.urlencode(
                            dict(schema_version=schema_version))
                        #
                        # redirect to actual changeset syntax validation procedure
                        return redirect('%s?%s' % (url, query_string))

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
                    thread = changeset_review_logic.changeset_review(
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
                models.Role.ROLE_DEVELOPER,
                models.Role.ROLE_DBA,
                models.Role.ROLE_ADMIN])

        if user_has_access:
            servers = models.Server.objects.all()

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
                models.Role.ROLE_DEVELOPER,
                models.Role.ROLE_DBA,
                models.Role.ROLE_ADMIN])

        if user_has_access:
            if id:
                server = models.Server.objects.get(pk=int(id))
            else:
                server = models.Server()
            if request.method == 'POST':
                form = forms.ServerForm(request.POST, instance=server)
                if form.is_valid():
                    server = form.save()
                    msg = u'Server [id=%s] was %s.' % (
                        server.id, u'updated' if id else u'created')
                    messages.success(request, msg)
                    log.info(msg)
                    return redirect('schemanizer_server_list')
            else:
                form = forms.ServerForm(instance=server)
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
                models.Role.ROLE_DEVELOPER,
                models.Role.ROLE_DBA,
                models.Role.ROLE_ADMIN])

        if user_has_access:
            server = models.Server.objects.get(pk=int(id))
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
def schema_version_create(
        request, server_id,
        template='schemanizer/schema_version_create.html'):
    """View for selecting schema to save."""

    user_has_access = False
    try:
        user = request.user.schemanizer_user
        role_name = user.role.name
        user_has_access = (
            role_name in [
                models.Role.ROLE_DEVELOPER,
                models.Role.ROLE_DBA,
                models.Role.ROLE_ADMIN])

        if user_has_access:
            server = models.Server.objects.get(pk=int(server_id))
            conn_opts = {}
            conn_opts['host'] = server.hostname
            #if settings.AWS_MYSQL_PORT:
            #    conn_opts['port'] = settings.AWS_MYSQL_PORT
            if server.port:
                conn_opts['port'] = server.port
            if settings.AWS_MYSQL_USER:
                conn_opts['user'] = settings.AWS_MYSQL_USER
            if settings.AWS_MYSQL_PASSWORD:
                conn_opts['passwd'] = settings.AWS_MYSQL_PASSWORD
            conn = MySQLdb.connect(**conn_opts)
            schema_choices = []
            with conn as cur:
                cur.execute('SHOW DATABASES')
                rows = cur.fetchall()
                for row in rows:
                    schema_choices.append((row[0], row[0]))

            if request.method == 'POST':
                form = forms.SelectRemoteSchemaForm(request.POST)
                form.fields['schema'].choices = schema_choices

                if form.is_valid():
                    schema = form.cleaned_data['schema']
                    structure = utils.mysql_dump(schema, **conn_opts)

                    #
                    # Save dump as latest version for the schema
                    #
                    database_schema, __ = models.DatabaseSchema.objects.get_or_create(
                        name=schema)
                    checksum = utils.schema_hash(structure)
                    create_schema = True
                    try:
                        schema_version = models.SchemaVersion.objects.get(
                            database_schema=database_schema,
                            checksum=checksum)
                        schema_version.ddl=structure
                        schema_version.save()
                        msg = u'Schema version for database schema `%s` was updated.' % (
                            database_schema.name,)
                    except ObjectDoesNotExist:
                        models.SchemaVersion.objects.create(
                            database_schema=database_schema,
                            ddl=structure,
                            checksum=utils.schema_hash(structure))
                        msg = u'New schema version for database schema `%s` was saved.' % (
                            database_schema.name,)
                    log.info(msg)
                    messages.success(request, msg)
                    return redirect('schemanizer_server_list')

            else:
                form = forms.SelectRemoteSchemaForm()
                form.fields['schema'].choices = schema_choices
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
                models.Role.ROLE_DEVELOPER,
                models.Role.ROLE_DBA,
                models.Role.ROLE_ADMIN])

        if user_has_access:
            database_schemas = models.DatabaseSchema.objects.all()
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
                models.Role.ROLE_DEVELOPER,
                models.Role.ROLE_DBA,
                models.Role.ROLE_ADMIN])

        database_schema = request.GET.get('database_schema', None)

        if user_has_access:
            schema_versions = models.SchemaVersion.objects.all()
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
                models.Role.ROLE_DEVELOPER,
                models.Role.ROLE_DBA,
                models.Role.ROLE_ADMIN])

        if user_has_access:
            r = models.SchemaVersion.objects.get(pk=int(schema_version_id))
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
                models.Role.ROLE_DEVELOPER,
                models.Role.ROLE_DBA,
                models.Role.ROLE_ADMIN])

        if user_has_access:
            qs = models.Environment.objects.all()
            can_add = can_update = can_delete = role_name in [
                models.Role.ROLE_DBA, models.Role.ROLE_ADMIN]
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
                models.Role.ROLE_DBA,
                models.Role.ROLE_ADMIN])

        if user_has_access:
            if environment_id:
                r = models.Environment.objects.get(pk=int(environment_id))
            else:
                r = models.Environment()
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
                models.Role.ROLE_DBA,
                models.Role.ROLE_ADMIN])

        if user_has_access:
            r = models.Environment.objects.get(pk=int(environment_id))
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
            models.Role.ROLE_DEVELOPER, models.Role.ROLE_DBA,
            models.Role.ROLE_ADMIN)
        if user_has_access:
            if request.method == 'POST':
                for k, v in request.POST.iteritems():
                    if k.startswith('server_'):
                        name, hostname, port = v.split(',')
                        with transaction.commit_on_success():
                            qs = models.Server.objects.filter(
                                hostname=hostname, port=port)
                            if not qs.exists():
                                models.Server.objects.create(
                                    name=name, hostname=hostname, port=port)
                                messages.info(
                                    request,
                                    u'Server %s was added.' % (hostname,))
                return redirect('schemanizer_server_list')
            else:
                mysql_servers = utils.discover_mysql_servers(
                    settings.NMAP_HOSTS, settings.NMAP_PORTS)

        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))

