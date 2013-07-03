import logging
from celery import task, current_task, states
from changesets import models as changesets_models
from users import models as users_models
from servers import models as servers_models
from . import changeset_apply

log = logging.getLogger(__name__)


@task(ignore_result=True)
def apply_changeset(changeset_pk, applied_by_user_pk, server_pk):
    """Applies changeset."""
    try:

        changeset = changesets_models.Changeset.objects.get(pk=changeset_pk)
        applied_by = users_models.User.objects.get(pk=applied_by_user_pk)
        server = servers_models.Server.objects.get(pk=server_pk)

        messages = []

        current_task.update_state(
            state=states.STARTED,
            meta=dict(
                changeset_id=changeset_pk,
                user_id=applied_by_user_pk,
                server_id=server_pk,
                messages=messages
            ))

        def message_callback(message, message_type, extra=None):
            messages.append(dict(
                message=message,
                message_type=message_type,
                extra=extra))
            current_task.update_state(
                state=states.STARTED,
                meta=dict(
                    changeset_id=changeset_pk,
                    user_id=applied_by_user_pk,
                    server_id=server_pk,
                    messages=messages))

        changeset_apply_obj = changeset_apply.apply_changeset(
            changeset, applied_by, server,
            message_callback,
            task_id=current_task.request.id)

        messages.append(dict(
            message='Changeset apply job completed.',
            message_type='info',
            extra=None))

        current_task.update_state(
            state=states.STARTED,
            meta=dict(
                changeset_id=changeset_pk,
                user_id=applied_by_user_pk,
                server_id=server_pk,
                messages=messages,
                changeset_detail_apply_ids=
                    changeset_apply_obj.changeset_detail_apply_ids))
    except:
        log.exception('EXCEPTION')
        raise