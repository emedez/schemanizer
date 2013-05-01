import json
from optparse import make_option
from pprint import pprint as pp

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import requests


def requests_get(url, params=None):
    r = requests.get(url, params=params, auth=(settings.CHANGESET_REPO_USER, settings.CHANGESET_REPO_PASSWORD))
    if r.status_code != 200:
        print 'status_code = %s' % (r.status_code,)
    return r


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
            pp(commit)


class Command(BaseCommand):
    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        get_commits()

