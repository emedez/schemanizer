"""Email-related logic."""

import logging

from emails.email_functions import send_mail

from users.models import Role, User

log = logging.getLogger(__name__)





def send_changeset_submission_through_repo_failed_mail(
        changeset_content, error_message, file_data, commit_data):
    """Sends changeset-submission-through-repo-failed email."""

    # recipients
    to = list(
        User.objects.values_list('email', flat=True)
        .filter(role__name=Role.ROLE_DBA))

    committer_user = None
    if 'committer' in commit_data and 'login' in commit_data['committer']:
        user_qs = User.objects.filter(
            github_login=commit_data['committer']['login'])
        if user_qs.exists():
            committer_user = user_qs[0]
    if committer_user and committer_user.email not in to:
        to.append(committer_user.email)

    if to:
        subject = u'Changeset submission through repository failed.'
        lines = []

        lines.append(u'Changeset data from repo')
        lines.append(u'========================')
        lines.append(u'')
        lines.append(u'Filename: %s' % (file_data['filename'],))
        lines.append(u'')
        lines.append(u'Content')
        lines.append(u'-------')
        lines.append(u'%s' % (changeset_content,))
        lines.append(u'')
        lines.append(
            u'Changeset submission process failed with the following '
            u'message:')
        lines.append(
            u'-------------------------------------------------------'
            u'--------')

        lines.append(u'%s' % (error_message,))

        send_mail(subject=subject, body=u'\n'.join(lines), to=to)

        log.info(
            u"New changeset-sumission-through-repository-failed email sent "
            u"to: %s" % (to,))

    else:
        log.warn(
            'Changeset-submission-through-repo-failed email has no '
            'recipients.')

















