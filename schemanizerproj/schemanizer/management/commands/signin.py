import getpass

from django.conf import settings
from django.contrib.auth import authenticate
from django.core.management.base import BaseCommand, CommandError

import requests
from cmd2 import Cmd, make_option, options
from requests.auth import HTTPBasicAuth
from texttable import Texttable

class Command(BaseCommand):
    option_list = BaseCommand.option_list

    def handle(self, *args, **options):
        if len(args) != 1:
            raise CommandError, "signin command requires 1 argument(username)."
        username = args[0]
        passwd = getpass.getpass("Enter schemanizer password for user '%s':" % (username))
        user = authenticate(username=username, password=passwd)
        if user is not None:
            cli = SchemanizerCLI(user=user, username=username, passwd=passwd)
            cli.cmdloop()
        else:
            print 'Invalid login.'

class SchemanizerCLI(Cmd):
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.username = kwargs.pop('username')
        self.passwd = kwargs.pop('passwd')
        self.api_auth = HTTPBasicAuth(self.username, self.passwd)
        self.prompt = 'Schemanizer(%s)> ' % (self.username)
        Cmd.__init__(self, *args, **kwargs)

    def default(self, line):
        # For some reason, the CLI interprets the signin and <username> as commands so ignore the invalid syntax for these
        if len(self.history) <= 2:
            return ''
        else:
            return Cmd.default(self, line)
    
    def do_schemanizer_list(self, arg, opts=None):
        '''Show changesets needing review.'''
        changesets = requests.get('%s/api/v1/changeset/' % settings.SCHEMANIZER_BASE_URL, 
                                params={'review_status': 'needs'},
                                auth=self.api_auth)
        objects = changesets.json().get('objects')
        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_align(['c', 'c', 'l', 'c'])
        table.set_cols_width([10, 10, 40, 10])
        rows = [['Changeset ID', 'Changeset Detail ID', 'Description', 'Submitted By']]
        for cs in objects:
            details = requests.get('%s/api/v1/changeset_detail/' % settings.SCHEMANIZER_BASE_URL,
                                params={'changeset__id': cs.get('id')},
                                auth=self.api_auth)
            detail_objects = details.json().get('objects')
            for detail in detail_objects:
                user = requests.get('%s%s' % (settings.SCHEMANIZER_BASE_URL, cs.get('submitted_by')),
                                    auth=self.api_auth)
                user_detail = user.json()
                rows.append([cs.get('id'), detail.get('id'), detail.get('description'), user_detail.get('name')])
        table.add_rows(rows)
        print 'Changesets That Need To Be Reviewed:'
        print table.draw()
        
    def do_schemanizer_show(self, arg, opts=None):
        print arg
