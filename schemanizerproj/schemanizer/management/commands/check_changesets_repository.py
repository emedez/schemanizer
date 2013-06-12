import base64
import json
import logging
from optparse import make_option
import pprint
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

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
    if r.status_code != 200:
        print 'status_code = %s' % (r.status_code,)
    return r


def process_file(f):
    try:
        filename = f['filename']
        #print u'status: %s' % (f['status'],)

        if f['status'] == 'added':
            if models.Changeset.objects.filter(
                    repo_filename=filename).exists():
                return
            msg = u'File: %s' % (filename,)
            print msg
            log.debug(msg)
            r = requests_get(f['contents_url'])
            if r.status_code == 200:
                data = json.loads(r.text)
                content = base64.b64decode(data['content'])
                yaml_obj = yaml.load(content)
                if not isinstance(yaml_obj, dict):
                    raise exceptions.Error('File format is invalid.')
                # msg = pprint.pformat(yaml_obj)
                # print msg
                # log.debug(msg)
                changeset = changeset_logic.save_changeset_yaml(
                    yaml_obj, filename)
                if changeset:
                    msg = u'Changeset [id=%s] was submitted.' % (changeset.id,)
                    print msg
                    log.debug(msg)
                print
            else:
                msg = u'Aborting, HTTP status code was %s.' % (r.status_code,)
                print msg
                log.error(msg)
        # else:
        #     msg = u'Ignored file: %s' % (filename,)
        #     print msg
        #     log.debug(msg)
    except Exception, e:
        msg = 'ERROR %s: %s' % (type(e), e)
        sys.stderr.write('%s\n' % (msg,))
        log.exception(msg)


def get_commit(url):
    r = requests_get(url)
    if r.status_code == 200:
        commit = json.loads(r.text)
        for f in commit['files']:
            process_file(f)
            print ''
    else:
        print u'Aborting, HTTP status code was %s.' % (r.status_code,)


def get_commits(path=None, since=None):
    params = {}
    if path:
        params['path'] = path
    if since:
        params['since'] = since

    url = settings.CHANGESET_REPO_URL
    r = requests_get(url, params)
    if r.status_code == 200:
        commits = json.loads(r.text)
        for commit in commits:
            get_commit(commit['url'])
    else:
        print u'Aborting, HTTP status code was %s.' % (r.status_code,)


class Command(BaseCommand):
    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        get_commits(path=settings.CHANGESET_PATH)

