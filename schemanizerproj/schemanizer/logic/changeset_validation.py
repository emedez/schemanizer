"""Changeset validation logic."""

import logging

from django.db import transaction
from django.utils import timezone
import sqlparse

from schemanizer import models, exceptions, utils
from schemanizer.logic import privileges as logic_privileges

log = logging.getLogger(__name__)

def changeset_validate_no_update_with_where_clause(changeset, user):
    """Changeset validate no update with where clause."""

    changeset = utils.get_model_instance(changeset, models.Changeset)
    user = utils.get_model_instance(user, models.User)
    now = timezone.now()

    if not logic_privileges.can_user_review_changeset(user, changeset):
        raise exceptions.PrivilegeError(
            u"User '%s' is not allowed to review changeset [id=%s]." % (
                user.name, changeset.id))

    has_errors = False
    results = dict(
        changeset_validation=None,
        changeset_tests=[],
        has_errors=has_errors)

    validation_results = []
    where_clause_found = False
    with transaction.commit_on_success():
        models.ChangesetValidation.objects.filter(
            changeset=changeset).delete()
        for changeset_detail in changeset.changeset_details.all():
            log.debug(u'Validating changeset detail...\nid: %s\napply_sql:\n%s' % (
                changeset_detail.id, changeset_detail.apply_sql))
            try:
                parsed = sqlparse.parse(changeset_detail.apply_sql)
                where_clause_found_on_apply_sql = False
                for stmt in parsed:
                    if stmt.get_type() in [u'INSERT', u'UPDATE', u'DELETE']:
                        for token in stmt.tokens:
                            if type(token) in [sqlparse.sql.Where]:
                                where_clause_found_on_apply_sql = True
                                break
                    if where_clause_found_on_apply_sql:
                        break
                if where_clause_found_on_apply_sql:
                    validation_results.append(
                        u'WHERE clause found on apply_sql (changeset detail ID: %s).' % (
                            changeset_detail.id,))
                    where_clause_found = True

                parsed = sqlparse.parse(changeset_detail.revert_sql)
                where_clause_found_on_revert_sql = False
                for stmt in parsed:
                    if stmt.get_type() in [u'INSERT', u'UPDATE', u'DELETE']:
                        for token in stmt.tokens:
                            if type(token) in [sqlparse.sql.Where]:
                                where_clause_found_on_revert_sql = True
                                break
                    if where_clause_found_on_revert_sql:
                        break
                if where_clause_found_on_revert_sql:
                    validation_results.append(
                        u'WHERE clause found on revert_sql. (changeset detail ID: %s).' % (
                            changeset_detail.id,))
                    where_clause_found = True
            except Exception, e:
                msg = 'ERROR %s: %s' % (type(e), e)
                log.exception(msg)
                validation_results.append(msg)
                has_errors = True

        validation_results_text = u''
        if validation_results:
            validation_results_text = u'\n'.join(validation_results)
        validation_type = models.ValidationType.objects.get(
            name=u'no update with where clause')
        changeset_validation = models.ChangesetValidation.objects.create(
            changeset=changeset,
            validation_type=validation_type,
            timestamp=now,
            result=validation_results_text)
        results['changeset_validation'] = changeset_validation

    log.info(u'Changeset no update with where clause validation was completed.')

    results['has_errors'] = has_errors or where_clause_found
    return results
