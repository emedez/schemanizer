import logging
import urllib
import warnings

import MySQLdb
warnings.filterwarnings('ignore', category=MySQLdb.Warning)

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms.models import inlineformset_factory
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from schemanizer import forms, exceptions
from schemanizer import models
from schemanizer import businesslogic

log = logging.getLogger(__name__)

MSG_USER_NO_ACCESS = u'You do not have access to this page.'

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