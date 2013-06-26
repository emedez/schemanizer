import logging
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, FormView, DeleteView
from utils import decorators, forms as utils_forms
from . import models, user_access, forms, user_functions, event_handlers

log = logging.getLogger(__name__)

class UserList(ListView):
    model = models.User

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(UserList, self).dispatch(request, *args, **kwargs)


class UserAdd(FormView):
    template_name='users/user_add.html'
    form_class = forms.UserAddForm
    initial = dict(role=1)
    success_url = reverse_lazy('users_user_list')

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(UserAdd, self).dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        try:
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            role_id = form.cleaned_data['role']
            password = form.cleaned_data['password']
            github_login = form.cleaned_data['github_login']
            role = models.Role.objects.get(id=role_id)

            schemanizer_user = user_functions.add_user(
                name, email, role, password, github_login)
            event_handlers.on_user_added(self.request, schemanizer_user)
            return super(UserAdd, self).form_valid(form)
        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            messages.error(self.request, msg)
            log.exception(msg)
            return self.render_to_response(
                context=self.get_context_data(form=form))


class UserUpdate(FormView):
    template_name='users/user_update.html'
    form_class = forms.UserUpdateForm
    success_url = reverse_lazy('users_user_list')

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(UserUpdate, self).dispatch(request, *args, **kwargs)

    def get_initial(self):
        # to be updated user
        user2 = models.User.objects.get(pk=int(self.kwargs['pk']))

        return dict(
            name=user2.name, email=user2.email, role=user2.role_id,
            github_login=user2.github_login)

    def form_valid(self, form):
        try:
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            role_id = form.cleaned_data['role']
            github_login = form.cleaned_data['github_login']
            role = models.Role.objects.get(id=role_id)
            schemanizer_user = user_functions.update_user(
                int(self.kwargs['pk']), name, email, role, github_login)
            event_handlers.on_user_updated(self.request, schemanizer_user)
            return super(UserUpdate, self).form_valid(form)
        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            messages.error(self.request, msg)
            log.exception(msg)
            return self.render_to_response(
                context=self.get_context_data(form=form))


class UserDelete(DeleteView):
    model = models.User
    success_url = reverse_lazy('users_user_list')

    @method_decorator(login_required)
    @decorators.check_access(user_access.check_access)
    def dispatch(self, request, *args, **kwargs):
        return super(UserDelete, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(UserDelete, self).get_context_data(**kwargs)
        context['form'] = utils_forms.SubmitForm()
        return context

    def delete(self, request, *args, **kwargs):
        to_be_deleted_object = self.get_object()
        return_value = super(UserDelete, self).delete(
            request, *args, **kwargs)
        event_handlers.on_user_deleted(self.request, to_be_deleted_object)
        return return_value