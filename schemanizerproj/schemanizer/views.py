import json
import logging
import urllib
import warnings

import MySQLdb
warnings.filterwarnings('ignore', category=MySQLdb.Warning)
import sqlparse

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import timezone

from schemanizer import businesslogic, exceptions, forms, models, utils

log = logging.getLogger(__name__)

MSG_USER_NO_ACCESS = u'You do not have access to this page.'
MSG_NOT_AJAX = u'Request must be a valid XMLHttpRequest.'

validate_changeset_syntax_threads = {}


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
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def confirm_delete_user(request, id, template='schemanizer/confirm_delete_user.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (models.Role.ROLE_ADMIN,)
        if user_has_access:
            id = int(id)
            to_be_del_user = models.User.objects.get(id=id)
            if request.method == 'POST':
                if 'confirm_delete' in request.POST:
                    with transaction.commit_on_success():
                        to_be_del_user.auth_user.delete()
                    log.info('User [id=%s] was deleted.' % (id,))
                    messages.success(request, 'User [id=%s] was deleted.' % (id,))
                    return redirect('schemanizer_users')
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def update_user(request, id, template='schemanizer/update_user.html'):
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
                    with transaction.commit_on_success():
                        businesslogic.update_user(id, name, email, role)
                    messages.success(request, u'User updated.')
                    return redirect('schemanizer_users')
            else:
                form = forms.UpdateUserForm(initial=initial)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


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
                    with transaction.commit_on_success():
                        businesslogic.create_user(name, email, role, password)
                    messages.success(request, u'User created.')
                    return redirect('schemanizer_users')
            else:
                form = forms.CreateUserForm(initial=initial)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


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
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def confirm_soft_delete_changeset(
        request, id, template='schemanizer/confirm_soft_delete_changeset.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        changeset = models.Changeset.objects.get(pk=int(id))
        user_has_access = changeset.can_be_soft_deleted_by(user)
        if user_has_access:
            if request.method == 'POST':
                if 'confirm_soft_delete' in request.POST:
                    with transaction.commit_on_success():
                        businesslogic.soft_delete_changeset(changeset)
                    messages.success(request, 'Changeset [id=%s] was soft deleted.' % (id,))
                    return redirect('schemanizer_changeset_list')
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_submit(request, template='schemanizer/changeset_edit.html'):
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
                changeset_form = forms.ChangesetForm(request.POST, instance=changeset)
                changeset_detail_formset = ChangesetDetailFormSet(request.POST, instance=changeset)
                if changeset_form.is_valid() and changeset_detail_formset.is_valid():
                    with transaction.commit_on_success():
                        changeset = businesslogic.changeset_submit(
                            changeset_form=changeset_form,
                            changeset_detail_formset=changeset_detail_formset,
                            user=user)
                    messages.success(request, u'Changeset submitted.')
                    return redirect('schemanizer_changeset_view', changeset.id)
            else:
                changeset_form = forms.ChangesetForm(instance=changeset)
                changeset_detail_formset = ChangesetDetailFormSet(instance=changeset)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def update_changeset(request, id, template='schemanizer/changeset_edit.html'):
    """Update changeset page."""
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in models.Role.ROLE_LIST
        if user_has_access:
            id = int(id)
            changeset = models.Changeset.objects.get(id=id)
            if changeset.can_be_updated_by(user):
                ChangesetDetailFormSet = inlineformset_factory(
                    models.Changeset, models.ChangesetDetail,
                    form=forms.ChangesetDetailForm,
                    extra=1, can_delete=False)
                if request.method == 'POST':
                    changeset_form = forms.ChangesetForm(request.POST, instance=changeset)
                    changeset_detail_formset = ChangesetDetailFormSet(request.POST, instance=changeset)
                    if changeset_form.is_valid() and changeset_detail_formset.is_valid():
                        with transaction.commit_on_success():
                            changeset =businesslogic.update_changeset(
                                changeset_form=changeset_form,
                                changeset_detail_formset=changeset_detail_formset,
                                user=user)
                        messages.success(request, u'Changeset updated.')
                        return redirect('schemanizer_changeset_view', changeset.id)
                else:
                    changeset_form = forms.ChangesetForm(instance=changeset)
                    changeset_detail_formset = ChangesetDetailFormSet(instance=changeset)
            else:
                messages.error(request, MSG_USER_NO_ACCESS)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_review(request, id, template='schemanizer/changeset_edit.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            models.Role.ROLE_ADMIN, models.Role.ROLE_DBA)
        if user_has_access:
            id = int(id)
            changeset = models.Changeset.objects.get(id=id)
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
                        changeset = businesslogic.changeset_review(
                            changeset_form=changeset_form,
                            changeset_detail_formset=changeset_detail_formset,
                            user=user)
                    messages.success(request, u'Changeset reviewed.')
                    return redirect('schemanizer_changeset_view', changeset.id)
            else:
                changeset_form = forms.ChangesetForm(instance=changeset)
                changeset_detail_formset = ChangesetDetailFormSet(
                    instance=changeset)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_view(request, id, template='schemanizer/changeset_view.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in models.Role.ROLE_LIST
        if user_has_access:
            id = int(id)
            changeset = models.Changeset.objects.select_related().get(id=id)
            if request.method == 'POST':
                try:
                    if u'submit_update' in request.POST:
                        return redirect(
                            'schemanizer_update_changeset', changeset.id)
                    elif u'submit_review' in request.POST:
                        return redirect(
                            'schemanizer_changeset_review', changeset.id)
                    elif u'submit_approve' in request.POST:
                        with transaction.commit_on_success():
                            businesslogic.changeset_approve(
                                changeset=changeset, user=user)
                        messages.success(request, u'Changeset approved.')
                    elif u'submit_reject' in request.POST:
                        with transaction.commit_on_success():
                            businesslogic.changeset_reject(
                                changeset=changeset, user=user)
                        messages.success(request, u'Changeset rejected.')
                    elif u'submit_delete' in request.POST:
                        return redirect(reverse(
                            'schemanizer_confirm_soft_delete_changeset',
                            args=[changeset.id]))
                    elif u'submit_validate_syntax' in request.POST:
                        return redirect(reverse(
                            'schemanizer_changeset_validate_syntax',
                            args=[changeset.id]))
                    elif u'submit_validate_no_update_with_where_clause' in request.POST:
                        return redirect(reverse(
                            'schemanizer_changeset_validate_no_update_with_where_clause',
                            args=[changeset.id]))
                    else:
                        messages.error(request, u'Unknown command.')
                except exceptions.NotAllowed, e:
                    log.exception('EXCEPTION')
                    messages.error(request, e.message)

            can_update = changeset.can_be_updated_by(user)
            can_review = changeset.can_be_reviewed_by(user)
            can_approve = changeset.can_be_approved_by(user)
            can_reject = changeset.can_be_rejected_by(user)
            can_soft_delete = changeset.can_be_soft_deleted_by(user)
            can_validate = businesslogic.user_can_validate_changeset(
                user, changeset)
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_list(request, template='schemanizer/changeset_list.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in models.Role.ROLE_LIST
        if user_has_access:
            changesets = models.Changeset.objects.get_not_deleted()
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
        can_soft_delete = user.role.name in (models.Role.ROLE_ADMIN,)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_apply_results(
        request, schema_version_id=None, changeset_id=None,
        template='schemanizer/changeset_apply_results.html'):
    """Changeset apply results page."""
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in models.Role.ROLE_LIST
        if user_has_access:
            schema_version = models.SchemaVersion.objects.get(pk=schema_version_id)
            changeset = models.Changeset.objects.get(pk=changeset_id)
            if schema_version.database_schema_id != changeset.database_schema_id:
                msg = u'Schema version and changeset are not for the same database schema.'
                log.error(
                    msg +
                    (u' schema_version_id=%s, changeset_id=%s' % (schema_version_id, changeset_id)))
                messages.error(request, msg)
            else:
                changeset_detail_applies = (
                    models.ChangesetDetailApply.objects.get_by_schema_version_changeset(
                        schema_version_id, changeset_id))
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_apply(request, template='schemanizer/changeset_apply.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            models.Role.ROLE_DBA, models.Role.ROLE_ADMIN)
        if user_has_access:

            # query string variables
            database_schema_id = request.GET.get('database_schema_id', None)
            if database_schema_id:
                database_schema_id = int(database_schema_id)
            schema_version_id = request.GET.get('schema_version_id', None)
            if schema_version_id:
                schema_version_id = int(schema_version_id)
            changeset_id = request.GET.get('changeset_id', None)
            if changeset_id:
                changeset_id = int(changeset_id)

            if request.method == 'POST':
                if u'select_database_schema_form_submit' in request.POST:
                    form = forms.SelectDatabaseSchemaForm(request.POST)
                    if form.is_valid():
                        database_schema_id = int(form.cleaned_data['database_schema'])
                        url = reverse('schemanizer_changeset_apply')
                        query_string = urllib.urlencode(dict(database_schema_id=database_schema_id))
                        return redirect('%s?%s' % (url, query_string))
                elif u'apply_changeset_form_submit' in request.POST:
                    database_schema = models.DatabaseSchema.objects.get(pk=database_schema_id)
                    form = forms.ApplyChangesetForm(request.POST, database_schema=database_schema)
                    if form.is_valid():
                        schema_version_id = int(form.cleaned_data['schema_version'])
                        changeset_id = int(form.cleaned_data['changeset'])
                        url = reverse('schemanizer_changeset_apply')
                        query_string = urllib.urlencode(dict(
                            database_schema_id=database_schema_id,
                            schema_version_id=schema_version_id,
                            changeset_id=changeset_id))
                        return redirect('%s?%s' % (url, query_string))
                elif u'continue_form_submit' in request.POST:
                    form = forms.ContinueForm(request.POST)
                    if form.is_valid():
                        with transaction.commit_on_success():
                            businesslogic.apply_changeset(
                                schema_version_id, changeset_id)
                        msg = u'Changeset was applied.'
                        log.info(msg)
                        messages.success(request, msg)
                        return redirect(reverse(
                            'schemanizer_changeset_apply_results',
                            args=[schema_version_id, changeset_id]))
                else:
                    msg = u'Unknown command.'
                    log.error(msg)
                    messages.error(request, msg)
            else:
                if not database_schema_id:
                    # No selected database schema yet? Ask one from user.
                    form = forms.SelectDatabaseSchemaForm()
                elif database_schema_id and schema_version_id and changeset_id:
                    # Everything is set, needs confirmation from user only.
                    schema_version = models.SchemaVersion.objects.get(pk=schema_version_id)
                    changeset = models.Changeset.objects.get(pk=changeset_id)
                    if schema_version.database_schema_id != changeset.database_schema_id:
                        messages.error(u'Schema version and changeset do not have the same database schema.')
                        url = reverse('schemanizer_changeset_apply')
                        query_string = urllib.urlencode(dict(
                            database_schema_id=database_schema_id))
                        return redirect('%s?%s' % (url, query_string))
                    else:
                        form = forms.ContinueForm()
                else:
                    # Have user select schema version and changeset
                    database_schema = models.DatabaseSchema.objects.get(pk=database_schema_id)
                    form = forms.ApplyChangesetForm(database_schema=database_schema)

        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_view_apply_results(request, template='schemanizer/changeset_view_apply_results.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in models.Role.ROLE_LIST

        if user_has_access:

            database_schema_id = request.GET.get('database_schema_id', None)
            if database_schema_id:
                database_schema_id = int(database_schema_id)
                database_schema = models.DatabaseSchema.objects.get(pk=database_schema_id)

            schema_version_id = request.GET.get('schema_version_id', None)
            if schema_version_id:
                schema_version_id = int(schema_version_id)
                schema_version = models.SchemaVersion.objects.get(pk=schema_version_id)

            if request.method == 'POST':
                if u'select_database_schema_form_submit' in request.POST:
                    form = forms.SelectDatabaseSchemaForm(request.POST)
                    if form.is_valid():
                        database_schema_id = int(form.cleaned_data['database_schema'])
                        url = reverse('schemanizer_changeset_view_apply_results')
                        query_string = urllib.urlencode(dict(
                            database_schema_id=database_schema_id))
                        return redirect('%s?%s' % (url, query_string))
                elif u'select_schema_version_form_submit' in request.POST:
                    form = forms.SelectSchemaVersionForm(request.POST, database_schema=database_schema)
                    if form.is_valid():
                        schema_version_id = int(form.cleaned_data['schema_version'])
                        url = reverse('schemanizer_changeset_view_apply_results')
                        query_string = urllib.urlencode(dict(
                            database_schema_id=database_schema_id,
                            schema_version_id=schema_version_id))
                        return redirect('%s?%s' % (url, query_string))
                else:
                    messages.error(request, u'Unknown command.')
            else:
                if database_schema_id and schema_version_id:
                    applied_changesets = businesslogic.get_applied_changesets(schema_version)
                elif database_schema_id:
                    form = forms.SelectSchemaVersionForm(database_schema=database_schema)
                else:
                    form = forms.SelectDatabaseSchemaForm()
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_validate_no_update_with_where_clause(
        request, id, template='schemanizer/changeset_validate_no_update_with_where_clause.html'):
    """Changeset validate no update with where clause view."""

    user_has_access = False
    try:
        changeset = models.Changeset.objects.get(pk=int(id))
        user_has_access = businesslogic.user_can_validate_changeset(
            request.user.schemanizer_user, changeset)

        if user_has_access:
            validation_results = []

            for cd in changeset.changeset_details.all():
                msg = u"Validating [%s]... " % (cd.apply_sql)
                parsed = sqlparse.parse(cd.apply_sql)
                where_clause_found = False
                for stmt in parsed:
                    if stmt.get_type() in [u'INSERT', u'UPDATE', u'DELETE']:
                        for token in stmt.tokens:
                            if type(token) in [sqlparse.sql.Where]:
                                msg += u'WHERE clause found!'
                                where_clause_found = True
                                break
                    if where_clause_found:
                        break
                if where_clause_found:
                    validation_results.append(u'Changeset Detail [id=%s] contains WHERE clause.' % (cd.id,))
                    messages.error(request, msg)
                else:
                    msg += u'OK.'
                    messages.success(request, msg)

            validation_results_text = u''
            if validation_results:
                validation_results_text = u'\n'.join(validation_results)
            validation_type = models.ValidationType.objects.get(name=u'no update with where clause')
            models.ChangesetValidation.objects.create(
                changeset=changeset,
                validation_type=validation_type,
                timestamp=timezone.now(),
                result=validation_results_text)

            msg = u'Changeset no update with where clause validation was completed.'
            log.info(msg)

            if len(validation_results_text) <= 0:
                validation_results_text = '< No Errors >'
            msg = u'Results:\n%s' % (validation_results_text,)
            log.info(msg)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_validate_syntax(request, id, template='schemanizer/changeset_validate_syntax.html'):
    """Validate changeset syntax view."""

    user_has_access = False
    try:
        request_id = utils.generate_request_id(request)
        changeset = models.Changeset.objects.get(pk=int(id))
        user_has_access = businesslogic.user_can_validate_changeset(request.user.schemanizer_user, changeset)
        schema_version = request.GET.get('schema_version', None)
        if schema_version:
            schema_version = models.SchemaVersion.objects.get(pk=int(schema_version))

        if user_has_access:
            if request.method == 'POST':

                if u'select_schema_version_form_submit' in request.POST:
                    #
                    # process select schema version form submission
                    #
                    select_schema_version_form = forms.SelectSchemaVersionForm(
                        request.POST, database_schema=changeset.database_schema)
                    if select_schema_version_form.is_valid():
                        schema_version = int(select_schema_version_form.cleaned_data['schema_version'])
                        url = reverse('schemanizer_changeset_validate_syntax', args=[changeset.id])
                        query_string = urllib.urlencode(dict(schema_version=schema_version))
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
                    # proceed with changeset syntax validation.
                    #
                    thread = businesslogic.validate_changeset_syntax(changeset, schema_version, request_id)
                    validate_changeset_syntax_threads[request_id] = thread
                    validate_changeset_syntax_started = True

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

    return render_to_response(template, locals(), context_instance=RequestContext(request))


def changeset_validate_syntax_status(
        request, request_id,
        messages_template='schemanizer/changeset_validate_syntax_status_messages.html'):
    """Checks changeset validate syntax status."""

    if not request.is_ajax():
        return HttpResponseForbidden(MSG_NOT_AJAX)

    data = {}
    try:
        if not request.user.is_authenticated():
            raise Exception('Login is required.')

        t = validate_changeset_syntax_threads.get(request_id, None)
        if not t:
            #
            # There was no running thread associated with the request_id,
            # It is either request ID is invalid or thread had completed
            # already and was removed from the dictionary.
            #
            data['error'] = u'Invalid request ID.'

        else:
            data['thread_is_alive'] = t.is_alive()
            data['thread_errors'] = t.errors
            data['thread_messages'] = t.messages
            data['thread_messages_html'] = render_to_string(
                messages_template, {'thread_messages': t.messages},
                context_instance=RequestContext(request))
            data['thread_changeset_was_validated'] = t.changeset_was_validated

            if not t.is_alive():
                #
                # Remove dead threads from dictionary.
                #
                validate_changeset_syntax_threads.pop(request_id, None)

        data_json = json.dumps(data)
    except Exception, e:
        log.exception('EXCEPTION')
        data = dict(error=u'%s' % (e,))
        data_json = json.dumps(data)

    return HttpResponse(data_json, mimetype='application/json')

