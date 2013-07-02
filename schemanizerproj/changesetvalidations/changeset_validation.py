import logging
from django.utils import timezone
import sqlparse
from . import models

log = logging.getLogger(__name__)


class ChangesetValidatorNoUpdateWithWhereClause(object):
    def __init__(self, changeset):
        super(ChangesetValidatorNoUpdateWithWhereClause, self).__init__()

        self.validation_type = models.ValidationType.objects.get(
            name='no update with where clause')
        self.changeset = changeset
        self.validation_log_items = []
        self.where_clause_found = False
        self.has_errors = False
        self.changeset_validation = None

    def validate_statement(self, changeset_detail, field_name):
        parsed = sqlparse.parse(getattr(changeset_detail, field_name))
        where_clause_found_= False
        for parsed_statement in parsed:
            if parsed_statement.get_type() in [u'INSERT', u'UPDATE', u'DELETE']:
                for token in parsed_statement.tokens:
                    if type(token) in [sqlparse.sql.Where]:
                        where_clause_found = True
                        break
            if where_clause_found:
                break
        if where_clause_found:
            self.validation_log_items.append(
                u'WHERE clause found on %s (changeset detail ID: %s).' % (
                    field_name, changeset_detail.id,))
            self.where_clause_found = True

    def validate_changeset_detail(self, changeset_detail):
        try:
            self.validate_statement(changeset_detail, 'apply_sql')
            self.validate_statement(changeset_detail, 'revert_sql')

        except Exception, e:
            self.has_errors = True
            msg = 'ERROR %s: %s' % (type(e), e)
            self.validation_log_items.append(msg)
            log.exception(msg)

    def run_validator(self):
        """Changeset validate no update with where clause."""

        models.ChangesetValidation.objects.filter(
            changeset=self.changeset).delete()
        for changeset_detail in self.changeset.changesetdetail_set.all():
            self.validate_changeset_detail(changeset_detail)

        validation_log = u'\n'.join(self.validation_log_items)
        self.changeset_validation = models.ChangesetValidation.objects.create(
            changeset=self.changeset,
            validation_type=self.validation_type,
            timestamp=timezone.now(),
            result=validation_log)

        self.has_errors = self.has_errors or self.where_clause_found


validator_map = {
    #'no update with where clause': ChangesetValidatorNoUpdateWithWhereClause
}


def run_validators(changeset):
    validation_types = models.ValidationType.objects.all()
    validation_results = []
    for validation_type in validation_types:
        if validation_type.name in validator_map:
            klass = validator_map[validation_type.name]
            instance = klass(changeset)
            instance.run_validator()
            validation_results.append(dict(
                has_errors=instance.has_errors,
                changeset_validation=instance.changeset_validation,
                validation_type=validation_type))
    return validation_results

