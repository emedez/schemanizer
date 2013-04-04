import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
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
    user = request.user.schemanizer_user
    user_has_access = user.role.name in models.Role.ROLE_LIST

    if user.role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
        show_to_be_reviewed_changesets = True
        changesets = models.Changeset.objects.get_needs_review()

    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def confirm_delete_user(request, id, template='schemanizer/confirm_delete_user.html'):
    user = request.user.schemanizer_user
    user_has_access = user.role.name in (models.Role.ROLE_ADMIN,)

    if user_has_access:
        id = int(id)
        to_be_del_user = models.User.objects.get(id=id)
        if request.method == 'POST':
            if 'confirm_delete' in request.POST:
                to_be_del_user.auth_user.delete()
                log.info('User [id=%s] was deleted.' % (id,))
                messages.success(request, 'User [id=%s] was deleted.' % (id,))
                return redirect('schemanizer_users')
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def update_user(request, id, template='schemanizer/update_user.html'):
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
                businesslogic.update_user(id, name, email, role)
                messages.success(request, u'User updated.')
                return redirect('schemanizer_users')
        else:
            form = forms.UpdateUserForm(initial=initial)
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def user_create(request, template='schemanizer/user_create.html'):
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
                businesslogic.create_user(name, email, role, password)
                messages.success(request, u'User created.')
                return redirect('schemanizer_users')
        else:
            form = forms.CreateUserForm(initial=initial)
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def users(request, template='schemanizer/users.html'):
    user = request.user.schemanizer_user
    user_has_access = user.role.name in (models.Role.ROLE_ADMIN,)

    if user_has_access:
        users = models.User.objects.select_related().all()
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def confirm_soft_delete_changeset(request, id, template='schemanizer/confirm_soft_delete_changeset.html'):
    user = request.user.schemanizer_user
    user_has_access = user.role.name in (models.Role.ROLE_ADMIN,)

    if user_has_access:
        id = int(id)
        changeset = models.Changeset.objects.get(id=id)
        if request.method == 'POST':
            if 'confirm_soft_delete' in request.POST:
                businesslogic.soft_delete_changeset(changeset)
                messages.success(request, 'Changeset [id=%s] was soft deleted.' % (id,))
                return redirect('schemanizer_changesets')
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_submit(request, template='schemanizer/changeset_edit.html'):
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
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_review(request, id, template='schemanizer/changeset_edit.html'):
    user = request.user.schemanizer_user
    user_has_access = user.role.name in (models.Role.ROLE_ADMIN, models.Role.ROLE_DBA)

    if user_has_access:
        id = int(id)
        changeset = models.Changeset.objects.get(id=id)
        ChangesetDetailFormSet = inlineformset_factory(
            models.Changeset, models.ChangesetDetail,
            form=forms.ChangesetDetailForm,
            extra=1, can_delete=False)
        if request.method == 'POST':
            changeset_form = forms.ChangesetForm(request.POST, instance=changeset)
            changeset_detail_formset = ChangesetDetailFormSet(request.POST, instance=changeset)
            if changeset_form.is_valid() and changeset_detail_formset.is_valid():
                changeset = businesslogic.changeset_review(
                    changeset_form=changeset_form,
                    changeset_detail_formset=changeset_detail_formset,
                    user=user)
                messages.success(request, u'Changeset reviewed.')
                return redirect('schemanizer_changeset_view', changeset.id)
        else:
            changeset_form = forms.ChangesetForm(instance=changeset)
            changeset_detail_formset = ChangesetDetailFormSet(instance=changeset)
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_view(request, id, template='schemanizer/changeset_view.html'):
    user = request.user.schemanizer_user
    user_has_access = user.role.name in models.Role.ROLE_LIST

    if user_has_access:
        id = int(id)
        changeset = models.Changeset.objects.select_related().get(id=id)
        if request.method == 'POST':
            try:
                if u'submit_review' in request.POST:
                    return redirect('schemanizer_changeset_review', changeset.id)
                elif u'submit_approve' in request.POST:
                    businesslogic.changeset_approve(
                        changeset=changeset, user=user)
                    messages.success(request, u'Changeset approved.')
                elif u'submit_reject' in request.POST:
                    businesslogic.changeset_reject(
                        changeset=changeset, user=user)
                    messages.success(request, u'Changeset rejected.')
                else:
                    messages.error(request, u'Unknown command.')
            except exceptions.NotAllowed, e:
                log.exception('EXCEPTION')
                messages.error(request, e.message)

        can_review=changeset.can_be_reviewed_by(user)
        can_approve=changeset.can_be_approved_by(user)
        can_reject=changeset.can_be_rejected_by(user)
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changesets(request, template='schemanizer/changesets.html'):
    user = request.user.schemanizer_user
    user_has_access = user.role.name in models.Role.ROLE_LIST

    if user_has_access:
        changesets = models.Changeset.objects.get_not_deleted()
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    can_soft_delete = user.role.name in (models.Role.ROLE_ADMIN,)

    return render_to_response(template, locals(), context_instance=RequestContext(request))


