import codecs
import logging
import os
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
import markdown
from changesets import models as changesets_models
from users import models as users_models


log = logging.getLogger(__name__)

MSG_USER_NO_ACCESS = u'You do not have access to this page.'
MSG_NOT_AJAX = u'Request must be a valid XMLHttpRequest.'

review_threads = {}
apply_threads = {}


@login_required
def home(request, template='schemanizer/home.html'):
    user_has_access = False
    try:
        user = request.user.schemanizer_user
        user_has_access = user.role.name in users_models.Role.ROLE_LIST
        if user.role.name in [users_models.Role.ROLE_DBA, users_models.Role.ROLE_ADMIN]:
            show_to_be_reviewed_changesets = True
            can_apply_changesets = True
            changesets = changesets_models.Changeset.to_be_reviewed_objects.all()
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))


def readme(request, template='schemanizer/readme.html'):
    user_has_access = False
    try:
        readme_path = os.path.abspath(
            os.path.join(settings.PROJECT_ROOT, '..', 'README.md'))
        input_file = codecs.open(readme_path, mode="r", encoding="utf-8")
        html = markdown.markdown(input_file.read())
    except Exception, e:
        log.exception('EXCEPTION')
        messages.error(request, u'%s' % (e,))
    return render_to_response(
        template, locals(), context_instance=RequestContext(request))

