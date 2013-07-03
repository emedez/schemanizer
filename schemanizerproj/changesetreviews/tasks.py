import logging
import functools
from celery import task, states, current_task
from changesets import models as changesets_models
from schemaversions import models as schemaversions_models
from users import models as users_models
from . import changeset_review

log = logging.getLogger(__name__)


@task(ignore_result=True)
def review_changeset(
        changeset_pk, schema_version_pk=None, reviewed_by_user_pk=None):
    """Reviews changeset."""

    try:
        def message_callback(message, message_type, current_task):
            current_task.update_state(
                state=states.STARTED,
                meta=dict(
                    message=message,
                    message_type=message_type))

        message_callback = functools.partial(
            message_callback, current_task=current_task)

        changeset = changesets_models.Changeset.objects.get(pk=changeset_pk)
        schema_version = None
        if schema_version_pk:
            schema_version = schemaversions_models.SchemaVersion.objects.get(
                pk=schema_version_pk)
        reviewed_by = None
        if reviewed_by_user_pk:
            reviewed_by = users_models.User.objects.get(pk=reviewed_by_user_pk)

        changeset_review.review_changeset(
            changeset, schema_version, reviewed_by,
            message_callback=message_callback,
            task_id=current_task.request.id)

        current_task.update_state(
            state=states.STARTED,
            meta=dict(
                message='Changeset review task completed.',
                message_type='info'))
    except:
        log.exception('EXCEPTION')
        raise