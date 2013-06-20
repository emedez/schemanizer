import base64
import json
import logging
from optparse import make_option
import pprint
import string
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from dateutil import parser, relativedelta
import requests
import yaml

from schemanizer import exceptions, models
from schemanizer.logic import changeset_logic

log = logging.getLogger(__name__)


def requests_get(url, params=None, headers=None):
    if headers is None:
        headers = {}
    request_get_params = dict(
        url=url, params=params)

    if settings.AUTHORIZATION_TOKEN:
        headers.update({
            'Authorization': 'token %s' % (
                settings.AUTHORIZATION_TOKEN,)})
    request_get_params['headers'] = headers

    r = requests.get(**request_get_params)
    return r


def process_file(f, commit):
    from schemanizer import tasks

    try:
        filename = f['filename']
        status = f['status']
        commit_datetime = parser.parse(commit['commit']['author']['date'])
        msg = (u'Filename: %s\nStatus: %s\nCommit Datetime: %s' % (
            filename, status, commit_datetime))
        print msg
        log.debug(msg)

        repo_filename_exists = models.Changeset.objects.filter(
            repo_filename=filename).exists()

        if not repo_filename_exists and (
                status == 'added' or status == 'modified'):

            r = requests_get(f['contents_url'])
            if r.status_code == 200:
                content = None
                try:
                    data = json.loads(r.text)
                    content = base64.b64decode(data['content'])
                    yaml_obj = yaml.load(content)
                    if not isinstance(yaml_obj, dict):
                        raise exceptions.Error('File format is invalid.')
                    changeset = changeset_logic.save_changeset_yaml(
                        yaml_obj, f, commit)
                    if changeset:
                        msg = u'Changeset [id=%s] was submitted.' % (
                            changeset.id,)
                        print msg
                        log.debug(msg)
                except Exception, e:
                    msg = 'ERROR %s: %s' % (type(e), e)
                    sys.stderr.write('%s\n' % (msg,))
                    log.exception(msg)
                    if not content:
                        content = ''
                    tasks.send_changeset_submission_through_repo_failed_mail.delay(
                        content, msg, f, commit)

                print
            else:
                msg = u'Aborting, HTTP status code was %s.' % (r.status_code,)
                print msg
                log.error(msg)

        elif repo_filename_exists and status == 'added':
            msg = 'File was ignored, it has been submitted previously.'
            print msg
            log.debug(msg)

        elif repo_filename_exists and status == 'modified':
            r = requests_get(f['contents_url'])
            if r.status_code == 200:
                content = None
                try:
                    data = json.loads(r.text)
                    content = base64.b64decode(data['content'])
                    yaml_obj = yaml.load(content)
                    if not isinstance(yaml_obj, dict):
                        raise exceptions.Error('File format is invalid.')
                    changeset = changeset_logic.update_changeset_yaml(
                        yaml_obj, f, commit)
                    if changeset:
                        msg = u'Changeset [id=%s] was updated.' % (
                            changeset.id,)
                        print msg
                        log.debug(msg)
                    else:
                        print 'Changeset was not processed.'
                except Exception, e:
                    msg = 'ERROR %s: %s' % (type(e), e)
                    sys.stderr.write('%s\n' % (msg,))
                    log.exception(msg)
                    if not content:
                        content = ''
                    tasks.send_changeset_submission_through_repo_failed_mail.delay(
                        content, msg, f, commit)

                print
            else:
                msg = u'Aborting, HTTP status code was %s.' % (r.status_code,)
                print msg
                log.error(msg)

        else:
            msg = 'File was ignored.'
            print msg
            log.debug(msg)

    except Exception, e:
        msg = 'ERROR %s: %s' % (type(e), e)
        sys.stderr.write('%s\n' % (msg,))
        log.exception(msg)


def get_commit(url):
    r = requests_get(url)
    if r.status_code == 200:
        commit = json.loads(r.text)
        for f in commit['files']:
            process_file(f, commit)
            print ''
    else:
        print u'Aborting, HTTP status code was %s.' % (r.status_code,)


def get_commits(path=None, since=None):
    params = dict(per_page=settings.GITHUB_ITEMS_PER_PAGE)
    if path:
        params['path'] = path
    if since:
        params['since'] = since

    url = settings.CHANGESET_REPO_URL
    r = requests_get(url, params)

    oldest_to_latest_commits = []
    if r.status_code == 200:
        commits = json.loads(r.text)
        for commit in commits:
            oldest_to_latest_commits.insert(0, commit)
        print 'Commits: %s, Total: %s\n' % (
            len(commits), len(oldest_to_latest_commits))

        while r and r.status_code == 200 and 'link' in r.headers:
            #pprint.pprint(r.headers)
            link = r.headers['link']
            r = None
            link_parts = link.split(',')
            for link_part in link_parts:
                url_part, rel_part = link_part.split(';')
                url_part = url_part.lstrip(
                    string.whitespace + '<').rstrip(
                    string.whitespace + '>')
                rel_part = rel_part.strip()
                if rel_part == 'rel="next"':
                    print 'Processing next page of commits: %s' % (url_part,)
                    r = requests_get(url_part)
                    if r.status_code == 200:
                        commits = json.loads(r.text)
                        for commit in commits:
                            oldest_to_latest_commits.insert(0, commit)

                        print 'Commits: %s, Total: %s\n' % (
                            len(commits), len(oldest_to_latest_commits))
                    else:
                        msg = 'Status code: %s' % (r.status_code)
                        print msg
                        log.error(msg)
                    break

        if oldest_to_latest_commits:
            for commit in oldest_to_latest_commits:
                get_commit(commit['url'])
        else:
            print 'No changesets to process.'

    else:
        print u'Aborting, HTTP status code was %s.' % (r.status_code,)
        pprint.pprint(r.text)


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--since', dest='since', default=None,
            help='ISO 8601 Date, for example, 2011-04-14T16:00:49Z. '
                 'Only commits after this date will be processed.'),
        make_option(
            '--since-hours', dest='since_hours', default=None, type='float',
            help='Only commits after the date/time '
                 'SINCE_HOURS ago will be processed. If not None, this '
                 'overrides the value of --since option'
        ),
    )

    def handle(self, *args, **options):
        since = options['since']
        since_hours = options['since_hours']
        if since_hours is not None:
            now = timezone.now()
            since_obj = now - relativedelta.relativedelta(hours=since_hours)
            since = since_obj.isoformat()
        if since is None:
            now = timezone.now()
            since_obj = now - relativedelta.relativedelta(
                hours=settings.CHANGESET_CHECK_HOUR_OFFSET)
            since = since_obj.isoformat()
        print 'Checking for changesets since %s...' % (since,)

        get_commits(path=settings.CHANGESET_PATH, since=since)

