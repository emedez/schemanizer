import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms.models import inlineformset_factory
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext

from schemanizer import forms
from schemanizer import models
from schemanizer import businesslogic

log = logging.getLogger(__name__)

MSG_USER_NO_ACCESS = u'You do not have access to this page.'

@login_required
def home(request, template='schemanizer/home.html'):
    user_has_access = businesslogic.user_role_is_in_roles(request.user, businesslogic.ROLE_LIST_ALL)
    role = request.user.schemanizer_user.role

    if role.name in (businesslogic.ROLE_DBA, ):
        changesets = businesslogic.get_to_be_reviewed_changesets()

    data = locals()
    data.update(dict(
        ROLE_ADMIN=businesslogic.ROLE_ADMIN,
        ROLE_DBA=businesslogic.ROLE_DBA,
        ROLE_DEVELOPER=businesslogic.ROLE_DEVELOPER))

    return render_to_response(template, data, context_instance=RequestContext(request))


@login_required
def users(request, template='schemanizer/users.html'):
    user_has_access = businesslogic.user_role_is_in_roles(
        request.user, (businesslogic.ROLE_ADMIN,))
    if user_has_access:
        users = models.User.objects.select_related().all()
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))


@login_required
def changeset_submit(request, template='schemanizer/changeset_submit.html'):
    user_has_access = businesslogic.user_role_is_in_roles(
        request.user, businesslogic.ROLE_LIST_ALL)
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


def changeset_view(request, id, template='schemanizer/changeset_view.html'):
    user_has_access = businesslogic.user_role_is_in_roles(
        request.user, businesslogic.ROLE_LIST_ALL)
    if user_has_access:
        id = int(id)
        changeset = models.Changeset.objects.select_related().get(id=id)
    else:
        messages.error(request, MSG_USER_NO_ACCESS)
    return render_to_response(template, locals(), context_instance=RequestContext(request))