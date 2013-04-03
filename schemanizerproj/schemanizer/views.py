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
    user_has_access = businesslogic.user_role_is_in_roles(request.user, models.Role.ROLE_LIST)
    role = request.user.schemanizer_user.role

    if role.name in (models.Role.ROLE_DBA, models.Role.ROLE_ADMIN):
        show_to_be_reviewed_changesets = True
        changesets = models.Changeset.objects.get_needs_to_be_reviewed()

    ROLE_ADMIN=models.Role.ROLE_ADMIN,
    ROLE_DBA=models.Role.ROLE_DBA,
    ROLE_DEVELOPER=models.Role.ROLE_DEVELOPER

    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def users(request, template='schemanizer/users.html'):
    user_has_access = businesslogic.user_role_is_in_roles(
        request.user, (models.Role.ROLE_ADMIN,))
    if user_has_access:
        users = models.User.objects.select_related().all()
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_submit(request, template='schemanizer/changeset_edit.html'):
    user_has_access = businesslogic.user_role_is_in_roles(
        request.user, models.Role.ROLE_LIST)
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
                    user=request.user.schemanizer_user)
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
    user_has_access = businesslogic.user_role_is_in_roles(
        request.user, (models.Role.ROLE_ADMIN, models.Role.ROLE_DBA))
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
                    user=request.user.schemanizer_user)
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
    user_has_access = businesslogic.user_role_is_in_roles(
        request.user, models.Role.ROLE_LIST)
    role = request.user.schemanizer_user.role
    if user_has_access:
        id = int(id)
        changeset = models.Changeset.objects.select_related().get(id=id)
        if request.method == 'POST':
            try:
                if u'submit_review' in request.POST:
                    return redirect('schemanizer_changeset_review', changeset.id)
                elif u'submit_approve' in request.POST:
                    businesslogic.changeset_approve(
                        changeset=changeset, auth_user=request.user)
                    messages.success(request, u'Changeset approved.')
                elif u'submit_reject' in request.POST:
                    businesslogic.changeset_reject(
                        changeset=changeset, auth_user=request.user)
                    messages.success(request, u'Changeset rejected.')
                else:
                    messages.error(request, u'Unknown command.')
            except exceptions.NotAllowed, e:
                log.exception('EXCEPTION')
                messages.error(request, e.message)

        can_review=changeset.can_be_reviewed_by(request.user)
        can_approve=changeset.can_be_approved_by(request.user)
        can_reject=changeset.can_be_rejected_by(request.user)
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changesets(request, template='schemanizer/changesets.html'):
    user_has_access = businesslogic.user_role_is_in_roles(
        request.user, models.Role.ROLE_LIST)
    if user_has_access:
        changesets = models.Changeset.objects.all()
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))