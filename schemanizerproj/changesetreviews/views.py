import json
import logging
from celery import states
from celery.result import AsyncResult
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, View
from djcelery import models as djcelery_models, humanize as djcelery_humanize
import yaml
from changesets import models as changesets_models
from changesettests import models as changesettests_models
from changesetvalidations import models as changesetvalidations_models
from schemaversions import models as schemaversions_models
from users import models as users_models
from utils import exceptions, decorators
from . import models, tasks
from schemanizer import utilities, forms
from schemanizer.logic import privileges_logic

log = logging.getLogger(__name__)
MSG_USER_NO_ACCESS = u'You do not have access to this page.'
MSG_NOT_AJAX = u'Request must be a valid XMLHttpRequest.'

# @login_required
# def changeset_reviews(
#         request, template='schemanizer/changeset_reviews.html'):
#     return render_to_response(
#         template, locals(), context_instance=RequestContext(request))


class ChangesetReviews(TemplateView):
    template_name = 'changesetreviews/changeset_reviews.html'

    @method_decorator(login_required)
    @decorators.check_access()
    def dispatch(self, request, *args, **kwargs):
        return super(ChangesetReviews, self).dispatch(request, *args, **kwargs)


# def ajax_changeset_reviews(
#         request, template='schemanizer/ajax_changeset_reviews.html'):
#     """Ajax view for on-going changeset review jobs."""
#
#     if not request.is_ajax():
#         return HttpResponseForbidden(MSG_NOT_AJAX)
#
#     data = {}
#     try:
#         if not request.user.is_authenticated():
#             raise Error('Login is required.')
#
#         task_states = djcelery_models.TaskState.objects.filter(
#             name='schemanizer.tasks.review_changeset',
#             state__in=states.UNREADY_STATES)
#         task_state_list = []
#         for task_state in task_states:
#             ar = AsyncResult(task_state.task_id)
#             result = ar.result
#             if result and isinstance(result, dict) and 'message' in result:
#                 show_message = True
#             else:
#                 show_message = False
#             kwargs_obj = {}
#             if task_state.kwargs:
#                 try:
#                     kwargs_obj = yaml.load(task_state.kwargs)
#                     if 'changeset' in kwargs_obj:
#                         kwargs_obj['changeset'] = long(kwargs_obj['changeset'])
#                 except:
#                     pass
#             changeset_id = kwargs_obj.get('changeset')
#             show_changeset_view_url = False
#             if changeset_id:
#                 show_changeset_view_url = (
#                     Changeset.objects.filter(pk=changeset_id).exists())
#
#             task_state_list.append(dict(
#                 task_id=task_state.task_id,
#                 tstamp=djcelery_humanize.naturaldate(task_state.tstamp),
#                 state=task_state.state,
#                 params=task_state.kwargs,
#                 #result=task_state.result,
#                 result=result,
#                 show_message=show_message,
#                 changeset_id=changeset_id,
#                 show_changeset_view_url=show_changeset_view_url,
#             ))
#
#         data['html'] = render_to_string(
#             template, locals(), context_instance=RequestContext(request))
#
#         data_json = json.dumps(data)
#
#     except Exception, e:
#         msg = 'ERROR %s: %s' % (type(e), e)
#         log.exception(msg)
#         data = dict(error=msg, html='')
#         data_json = json.dumps(data)
#
#     return HttpResponse(data_json, mimetype='application/json')


class AjaxChangesetReviews(View):
    def get(
            self, request,
            template_name='changesetreviews/ajax_changeset_reviews.html',
            *args, **kwargs):

        if not request.is_ajax():
            return HttpResponseForbidden(MSG_NOT_AJAX)

        data = {}
        try:
            if not request.user.is_authenticated():
                raise exceptions.Error('Login is required.')

            task_states = djcelery_models.TaskState.objects.filter(
                name='changesetreviews.tasks.review_changeset',
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
                        changesets_models.Changeset.objects.filter(
                            pk=changeset_id).exists())

                task_state_list.append(dict(
                    task_id=task_state.task_id,
                    tstamp=djcelery_humanize.naturaldate(task_state.tstamp),
                    state=task_state.state,
                    params=task_state.kwargs,
                    result=result,
                    show_message=show_message,
                    changeset_id=changeset_id,
                    show_changeset_view_url=show_changeset_view_url,
                ))

            data['html'] = render_to_string(
                template_name, locals(),
                context_instance=RequestContext(request))

            data_json = json.dumps(data)

        except Exception, e:
            msg = 'ERROR %s: %s' % (type(e), e)
            log.exception(msg)
            data = dict(error=msg, html='')
            data_json = json.dumps(data)

        return HttpResponse(data_json, mimetype='application/json')


@login_required
def changeset_review(
        request, changeset_id,
        template='changesetreviews/changeset_review.html'):
    user_has_access = False
    try:
        request_id = utilities.generate_request_id(request)
        changeset = changesets_models.Changeset.objects.get(pk=int(changeset_id))
        user = request.user.schemanizer_user
        user_has_access = privileges_logic.can_user_review_changeset(
            user, changeset)
        schema_version = request.GET.get('schema_version', None)
        if schema_version:
            schema_version = schemaversions_models.SchemaVersion.objects.get(
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

                        tasks.review_changeset.delay(
                            changeset_pk=changeset.pk,
                            schema_version_pk=schema_version,
                            reviewed_by_user_pk=user.pk)
                        messages.info(
                            request,
                            u'Changeset review has been started, email will '
                            u'be sent to interested parties when review '
                            u'procedure is completed.')

                        return redirect('changesetreviews_changeset_reviews')

                else:
                    #
                    # Invalid POST.
                    #
                    messages.error(request, u'Unknown command.')

            else:
                # #
                # # GET
                # #
                #
                # if schema_version:
                #     #
                #     # User has selected a schema version already,
                #     # proceed with changeset review.
                #     #
                #     thread = changeset_review_logic.start_changeset_review_thread(
                #         changeset, schema_version, user)
                #     review_threads[request_id] = thread
                #     thread_started = True
                #
                # else:
                #     #
                #     # No schema version was selected yet,
                #     # ask one from user
                #     #
                select_schema_version_form = forms.SelectSchemaVersionForm(
                    database_schema=changeset.database_schema)

        else:
            messages.error(request, MSG_USER_NO_ACCESS)

    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))

    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


@login_required
def result(
        request, changeset_id,
        template='changesetreviews/result.html'):
    user_has_access = False

    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in (
            users_models.Role.NAME.developer,
            users_models.Role.NAME.dba,
            users_models.Role.NAME.admin)
        if user_has_access:
            changeset = changesets_models.Changeset.objects.get(pk=int(changeset_id))
            changeset_review = None
            try:
                changeset_review = models.ChangesetReview.objects.get(
                    changeset=changeset)
            except ObjectDoesNotExist:
                pass
            if (
                    changeset.review_status in [
                        changesets_models.Changeset.REVIEW_STATUS_IN_PROGRESS,
                        changesets_models.Changeset.REVIEW_STATUS_APPROVED]):
                changeset_review_success = True
            if (
                    changeset.review_status ==
                        changesets_models.Changeset.REVIEW_STATUS_REJECTED):
                changeset_review_failed = True
            changeset_validations = (
                changesetvalidations_models.ChangesetValidation.objects
                .filter(changeset=changeset).order_by('id'))
            changeset_validation_ids = request.GET.get(
                'changeset_validation_ids', None)
            if changeset_validation_ids:
                changeset_validation_ids = [
                    int(id) for id in changeset_validation_ids.split(',')]
                changeset_validations = changeset_validations.filter(
                    id__in=changeset_validation_ids)
            changeset_tests = (
                changesettests_models.ChangesetTest.objects.filter(
                changeset_detail__changeset=changeset).order_by('id'))
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