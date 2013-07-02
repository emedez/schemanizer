import logging
from pprint import pformat
import urllib
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.forms.models import inlineformset_factory
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, ListView
from changesetapplies import models as changesetapplies_models
from users import models as users_models
from utils import decorators, exceptions
from . import models, forms, changeset_functions, user_access
from schemanizer.logic import privileges_logic

log = logging.getLogger(__name__)
MSG_USER_NO_ACCESS = u'You do not have access to this page.'


class ChangesetSubmit(TemplateView):
    template_name = 'changesets/changeset_update.html'

    @method_decorator(login_required)
    @decorators.check_access()
    def dispatch(self, request, *args, **kwargs):
        return super(ChangesetSubmit, self).dispatch(request, *args, **kwargs)

    def setup(self):
        self.changeset = models.Changeset()
        self.ChangesetDetailFormSet = inlineformset_factory(
            models.Changeset, models.ChangesetDetail,
            form=forms.ChangesetDetailForm,
            extra=1, can_delete=False)

    def get_context_data(self, **kwargs):
        context = super(ChangesetSubmit, self).get_context_data(**kwargs)
        context['changeset_form'] = self.changeset_form
        context['changeset_detail_formset'] = self.changeset_detail_formset
        return context

    def get(self, request, *args, **kwargs):
        self.setup()
        self.changeset_form = forms.ChangesetForm(instance=self.changeset)
        self.changeset_detail_formset = self.ChangesetDetailFormSet(
            instance=self.changeset)
        return super(ChangesetSubmit, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()
        self.changeset_form = forms.ChangesetForm(
            request.POST, instance=self.changeset)
        self.changeset_detail_formset = self.ChangesetDetailFormSet(
            request.POST, instance=self.changeset)

        try:

            valid_forms = (
                self.changeset_form.is_valid() and
                self.changeset_detail_formset.is_valid())
            if valid_forms:
                changeset = changeset_functions.submit_changeset(
                    changeset_form=self.changeset_form,
                    changeset_detail_formset=self.changeset_detail_formset,
                    submitted_by=request.user.schemanizer_user,
                    request=request)
                return redirect('changesetreviews_changeset_reviews')

        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            messages.error(request, msg)
            log.exception(msg)

        local_vars = locals()
        if 'self' in local_vars:
            del local_vars['self']

        return self.render_to_response(self.get_context_data(**local_vars))


class ChangesetList(ListView):
    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(ChangesetList, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return models.Changeset.not_deleted_objects.all()

    def get_context_data(self, **kwargs):
        context = super(ChangesetList, self).get_context_data(**kwargs)
        user = self.request.user.schemanizer_user
        changeset_qs = self.get_queryset()
        changeset_list = []
        for changeset in changeset_qs:
            extra=dict(
                can_apply=privileges_logic.can_user_apply_changeset(user, changeset),
                can_review=privileges_logic.can_user_review_changeset(user, changeset))
            changeset_list.append(dict(changeset=changeset, extra=extra))
        context['changeset_list'] = changeset_list
        return context


@login_required
def changeset_view(request, id, template='changesets/changeset_view.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            users_models.Role.NAME.developer,
            users_models.Role.NAME.dba,
            users_models.Role.NAME.admin)

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
                            'changesets_changeset_update', changeset.id)

                    elif u'submit_review' in request.POST:
                        #
                        # Set changeset review status to 'in_progress'
                        #
                        return redirect(
                            'changesetreviews_changeset_review',
                            changeset.id)

                    elif u'submit_approve' in request.POST:
                        #
                        # Approve changeset.
                        #
                        changeset_functions.approve_changeset(
                            changeset=changeset, approved_by=user,
                            request=request)
                        return redirect(
                            'changesets_changeset_view', changeset.pk)

                    elif u'submit_reject' in request.POST:
                        #
                        # Reject changeset.
                        #
                        changeset_functions.reject_changeset(
                            changeset=changeset, rejected_by=user,
                            request=request)
                        return redirect(
                            'changesets_changeset_view', changeset.pk)

                    elif u'submit_delete' in request.POST:
                        #
                        # Delete changeset.
                        #
                        return redirect(
                            'changesets_changeset_soft_delete',
                            changeset.id)

                    elif u'submit_apply' in request.POST:
                        #
                        # Apply changeset
                        #
                        return redirect(
                            'changesetapplies_changeset_apply',
                            changeset.id)

                    else:
                        messages.error(request, u'Unknown command.')
                        log.error(
                            u'Invalid post.\nrequest.POST=\n%s' % (
                                pformat(request.POST),))

                except Exception, e:
                    log.exception('EXCEPTION')
                    messages.error(request, u'%s' % (e,))

            changeset_applies = (
                changesetapplies_models.ChangesetApply.objects.filter(
                    changeset=changeset))

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
                changeset_apply_qs = changesetapplies_models.ChangesetApply.objects.filter(
                    changeset_action=changeset_action)
                if changeset_apply_qs.exists():
                    changeset_apply = changeset_apply_qs[0]
                    if changeset_apply.task_id:
                        changeset_applies_url = '%s?%s' % (
                            reverse('changesetapplies_changeset_applies'),
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


class ChangesetUpdate(TemplateView):
    template_name = 'changesets/changeset_update.html'

    @method_decorator(login_required)
    @decorators.check_access()
    def dispatch(self, request, *args, **kwargs):
        return super(ChangesetUpdate, self).dispatch(request, *args, **kwargs)

    def setup(self):
        self.user = self.request.user.schemanizer_user
        self.changeset = models.Changeset.objects.get(pk=int(self.kwargs['pk']))
        self.can_update_changeset = (
            privileges_logic.UserPrivileges(self.user).can_update_changeset(
                self.changeset))
        self.ChangesetDetailFormSet = inlineformset_factory(
            models.Changeset, models.ChangesetDetail,
            form=forms.ChangesetDetailForm, extra=1, can_delete=True)

        if not self.can_update_changeset:
            messages.error(self.request, MSG_USER_NO_ACCESS)

        self.changset_form = None
        self.changeset_detail_formset = None

    def get_context_data(self, **kwargs):
        context = super(ChangesetUpdate, self).get_context_data(**kwargs)
        context['changeset_form'] = self.changeset_form
        context['changeset_detail_formset'] = self.changeset_detail_formset
        return context

    def get(self, request, *args, **kwargs):
        self.setup()

        self.changeset_form = forms.ChangesetForm(instance=self.changeset)
        self.changeset_detail_formset = self.ChangesetDetailFormSet(
            instance=self.changeset)

        return super(ChangesetUpdate, self).get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        self.setup()

        try:
            if self.can_update_changeset:
                self.changeset_form = forms.ChangesetForm(
                    request.POST, instance=self.changeset)
                self.changeset_detail_formset = self.ChangesetDetailFormSet(
                    request.POST, instance=self.changeset)
                if self.changeset_form.is_valid() and self.changeset_detail_formset.is_valid():
                    changeset = changeset_functions.update_changeset(
                        changeset_form=self.changeset_form,
                        changeset_detail_formset=self.changeset_detail_formset,
                        updated_by=self.user, request=request)
                    return redirect(
                        'changesets_changeset_view', changeset.id)
        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            messages.error(request, msg)
            log.exception(msg)

        local_vars = locals()
        if 'self' in local_vars:
            del local_vars['self']

        return self.render_to_response(self.get_context_data(**local_vars))


@login_required
def changeset_soft_delete(request, pk,
                          template='changesets/changeset_soft_delete.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        changeset = models.Changeset.objects.get(pk=int(pk))
        user_has_access = (
            privileges_logic.UserPrivileges(user)
            .can_soft_delete_changeset(changeset))
        if user_has_access:
            if request.method == 'POST':
                changeset_functions.soft_delete_changeset(
                    changeset, user, request)
                return redirect('changesets_changeset_list')
        else:
            messages.error(request, MSG_USER_NO_ACCESS)
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))