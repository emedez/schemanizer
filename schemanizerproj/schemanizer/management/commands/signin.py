import getpass
import json
import logging
import time

from django.contrib.auth import authenticate
from django.contrib.sites.models import Site
from django.core.management.base import BaseCommand, CommandError

import requests
from cmd2 import Cmd, make_option, options
from requests.auth import HTTPBasicAuth
from texttable import Texttable

from changesets import models as changesets_models

log = logging.getLogger(__name__)


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
    schemanizer_header = 'Schemanizer commands (type help <topic>):'
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        self.username = kwargs.pop('username')
        self.passwd = kwargs.pop('passwd')
        self.api_auth = HTTPBasicAuth(self.username, self.passwd)
        self.site = Site.objects.get_current()
        self.prompt = 'Schemanizer(%s)> ' % (self.username)
        Cmd.__init__(self, *args, **kwargs)

    def default(self, line):
        # For some reason, the CLI interprets the signin and <username> as commands so ignore the invalid syntax for these
        if len(self.history) <= 2:
            return ''
        else:
            return Cmd.default(self, line)
    
    def do_help(self, arg):
        'List available commands with "help" or detailed help with "help cmd".'
        if arg:
            # XXX check arg syntax
            try:
                func = getattr(self, 'help_' + arg)
            except AttributeError:
                try:
                    doc=getattr(self, 'do_' + arg).__doc__
                    if doc:
                        self.stdout.write("%s\n"%str(doc))
                        return
                except AttributeError:
                    pass
                self.stdout.write("%s\n"%str(self.nohelp % (arg,)))
                return
            func()
        else:
            names = self.get_names()
            cmds_doc = []
            cmds_undoc = []
            cmds_schemanizer = []
            help = {}
            for name in names:
                if name[:5] == 'help_':
                    help[name[5:]]=1
            names.sort()
            # There can be duplicates if routines overridden
            prevname = ''
            for name in names:
                if name[:3] == 'do_':
                    if name == prevname:
                        continue
                    prevname = name
                    cmd=name[3:]
                    if cmd in help:
                        cmds_doc.append(cmd)
                        del help[cmd]
                    elif getattr(self, name).__doc__:
                        cmds_doc.append(cmd)
                    else:
                        cmds_undoc.append(cmd)
                    if cmd in ['list_changesets', 'create_changeset', 'show_changeset',
                            'review_changeset', 'approve_changeset', 'reject_changeset',
                            'apply_changeset']:
                        cmds_schemanizer.append(cmd)
            self.stdout.write("%s\n"%str(self.doc_leader))
            self.print_topics(self.doc_header,   cmds_doc,   15,80)
            self.print_topics(self.misc_header,  help.keys(),15,80)
            self.print_topics(self.undoc_header, cmds_undoc, 15,80)
            self.print_topics(self.schemanizer_header, cmds_schemanizer, 15,80)
    
    def do_list_changesets(self, arg, opts=None):
        '''Show changesets needing review.'''
        changesets = requests.get('http://%s/api/v1/changeset/' % self.site, 
                                params={'review_status': 'needs'},
                                auth=self.api_auth)
        objects = changesets.json().get('objects')
        table = Texttable()
        table.set_deco(Texttable.HEADER)
        table.set_cols_align(['c', 'c', 'c', 'c', 'c'])
        table.set_cols_width([5, 20, 15, 15, 10])
        rows = [['ID', 'Type', 'Classification', 'Version Control URL', 'Submitted By']]
        for cs in objects:
            user = requests.get('http://%s%s' % (self.site, cs.get('submitted_by')),
                                    auth=self.api_auth)
            user_detail = user.json()
            rows.append([cs.get('id'), cs.get('type'), cs.get('classification'),
                        cs.get('version_control_url'), user_detail.get('name')])
        table.add_rows(rows)
        print 'Changesets That Need To Be Reviewed:'
        print table.draw()
        
    def do_create_changeset(self, arg, opts=None):
        '''Create a new changeset'''

        #
        # database_schema_id
        #
        schema_id = self.pseudo_raw_input('Enter Schema ID: ')
        schema_id = int(schema_id)

        changeset_type = ''
        changeset_classification = ''
        changeset = {}
        review_version_id = None
        changeset_details = []

        #
        # type
        #
        type_choices = []
        for i,choice in enumerate(changesets_models.Changeset.TYPE_CHOICES):
            type_choices.append((i+1, choice[0]))
        found = False
        while not found:
            print 'Type Choices:'
            for choice in type_choices:
                print '\t%d - %s' % (choice[0], choice[1])
            type_int = self.pseudo_raw_input('Choose Type(enter corresponding number): ')
            type_int = int(type_int)
            for choice in type_choices:
                if type_int == choice[0]:
                    changeset_type = choice[1]
                    found = True
                    break
            if not found:
                print 'Invalid Choice.'

        #
        # classification
        #
        classification_choices = []
        for i,choice in enumerate(
                changesets_models.Changeset.CLASSIFICATION_CHOICES):
            classification_choices.append((i+1, choice[0]))
        found = False
        while not found:
            print 'Classification Choices:'
            for choice in classification_choices:
                print '\t%d - %s' % (choice[0], choice[1])
            classification_int = self.pseudo_raw_input('Choose Classification(enter corresponding number): ')
            classification_int = int(classification_int)
            for choice in classification_choices:
                if classification_int == choice[0]:
                    changeset_classification = choice[1]
                    found = True
                    break
            if not found:
                print 'Invalid Choice.'

        #
        # review_version_id
        #
        review_version_id = self.pseudo_raw_input('Review Version ID: ')
        if review_version_id:
            review_version_id = int(review_version_id)
        else:
            review_version_id = None

        changeset.update({
            'database_schema_id': schema_id,
            'type': changeset_type,
            'classification': changeset_classification,
        })
        if review_version_id:
            changeset.update({
                'review_version_id': review_version_id
            })

        #
        # ChangesetDetail
        #

        while True:
            enter_detail = self.pseudo_raw_input('Add Detail(Y/N): ')
            if enter_detail.upper() != 'Y':
                break
                
            description = ''
            apply_sql = ''
            revert_sql = ''

            description = self.pseudo_raw_input('Enter Description: ')
            apply_sql = self.pseudo_raw_input('Enter Apply SQL: ')
            revert_sql = self.pseudo_raw_input('Enter Revert SQL: ')
            apply_verification_sql = self.pseudo_raw_input(
                'Enter Apply Verification SQL: ')
            revert_verification_sql = self.pseudo_raw_input(
                'Enter Revert Verification SQL: ')
            changeset_details.append({
                'description': description,
                'apply_sql': apply_sql,
                'revert_sql': revert_sql,
                'apply_verification_sql': apply_verification_sql,
                'revert_verification_sql': revert_verification_sql
            })
            
        post = {
            'changeset': changeset,
            'changeset_details': changeset_details
        }
        r = requests.post(
            'http://%s/api/v1/changeset/submit/' % (self.site),
            data=json.dumps(post),
            auth=self.api_auth)

        if r.status_code == 200:
            print 'Adding changeset successful'
        else:
            print 'Adding changeset failed'
    
    def do_show_changeset(self, arg, opts=None):
        '''Show fields and details for a changeset.'''
        if arg:
            changeset_id = arg
            changeset = requests.get('http://%s/api/v1/changeset/%s' % (self.site, changeset_id),
                                    auth=self.api_auth)
            cs = changeset.json()
            details = requests.get('http://%s/api/v1/changeset_detail/' % self.site,
                                    params={'changeset__id': cs.get('id')},
                                    auth=self.api_auth)
            detail_objects = details.json().get('objects')
            user = requests.get('http://%s%s' % (self.site, cs.get('submitted_by')),
                                auth=self.api_auth)
            user_detail = user.json()
            schema = requests.get('http://%s%s' % (self.site, cs.get('database_schema')),
                                auth=self.api_auth)
            schema_detail = schema.json()
            print 'Changeset #%s' % cs.get('id')
            print
            print 'ID: %s' % cs.get('id')
            print 'Schema: %s' % schema_detail.get('name')
            print 'Submitted By: %s' % user_detail.get('name')
            print 'Review Status: %s' % cs.get('review_status')
            print 'Classification: %s' % cs.get('classification')
            print
            print 'Changeset Details:'
            for i, detail in enumerate(detail_objects):
                print '%d.\tID: %s' % (i+1, detail.get('id'))
                print '\tDescription: %s' % detail.get('description')
                print '\tType: %s' % detail.get('type')
                print '\tApply SQL: %s' % detail.get('apply_sql')
                print '\tRevert SQL: %s' % detail.get('revert_sql')
                print
        else:
            raise Exception, '*** Invalid syntax: show_changeset requires 1 argument(id).'
            
    def do_review_changeset(self, arg, opts=None):
        '''Run validations and tests for a changeset.'''
        if arg:
            changeset_id = arg
            schema_version_id = self.pseudo_raw_input('Enter Schema Version ID: ')
            post = {
                'schema_version_id': schema_version_id,
            }
            r = requests.post('http://%s/api/v1/changeset/review/%s/' % (self.site, changeset_id),
                                data=json.dumps(post),
                                auth=self.api_auth)
            response = r.json()
            # request_id = response.get('request_id')
            # thread_started = response.get('thread_started')
            task_id = response.get('task_id')
            # if thread_started:
            if task_id:
                # thread_is_alive = True
                task_active = True
                # while thread_is_alive:
                # while task_active:
                max_tries = 12
                tries = 0
                while True:
                    tries += 1
                    r = requests.get(
                        'http://%s/api/v1/changeset/review_status/%s/' % (
                            self.site, task_id),
                        auth=self.api_auth)
                    response = r.json()
                    # print response
                    task_active = response.get('task_active')
                    message = response.get('message')
                    # thread_messages = response.get('thread_messages', [])
                    # for message in thread_messages:
                    #     print message[1]
                    if message:
                        print message
                    if task_active is None:
                        if tries >= max_tries:
                            break
                    else:
                        if not task_active:
                            break
                    time.sleep(10)

                changeset_test_ids = response.get('changeset_test_ids', [])
                changeset_validation_ids = response.get(
                    'changeset_validation_ids', [])
                print
                print 'Validation Result Log:'
                for i,val_id in enumerate(changeset_validation_ids):
                    r = requests.get(
                        'http://%s/api/v1/changeset_validation/%d/' % (
                            self.site, val_id),
                        auth=self.api_auth)
                    response = r.json()
                    log = response.get('result')
                    print '%d. %s' % (i+1, log)
                print
                print 'Test Result Log:'
                for i,test_id in enumerate(changeset_test_ids):
                    r = requests.get(
                        'http://%s/api/v1/changeset_test/%d/' % (
                            self.site, test_id),
                        auth=self.api_auth)
                    response = r.json()
                    log = response.get('results_log')
                    print '%d. %s' % (i+1, log)
                print
                print '*** Changeset check successful.'
            else:
                raise Exception, '*** Changeset check failed: Unable to start changeset review.'
        else:
            raise Exception, '*** Invalid syntax: review_changeset requires 1 argument(id).'
            
    def do_approve_changeset(self, arg, opts=None):
        '''Approve a changeset'''
        if arg:
            changeset_id = arg
            r = requests.post('http://%s/api/v1/changeset/approve/%s/' % (self.site, changeset_id),
                                auth=self.api_auth)
            response = r.json()
            review_status = response.get('review_status')
            if review_status == 'approved':
                print 'Approved Changeset Details:'
                self.do_show_changeset(changeset_id)
                print
                print '*** Changeset approval successful.'
            else:
                raise Exception, '*** Changeset approval failed: Unable to approve changeset.'
        else:
            raise Exception, '*** Invalid syntax: approve_changeset requires 1 argument(id).'
            
    def do_reject_changeset(self, arg, opts=None):
        '''Reject a changeset'''
        if arg:
            changeset_id = arg
            r = requests.post('http://%s/api/v1/changeset/reject/%s/' % (self.site, changeset_id),
                                auth=self.api_auth)
            response = r.json()
            review_status = response.get('review_status')
            if review_status == 'rejected':
                print 'Rejected Changeset Details:'
                self.do_show_changeset(changeset_id)
                print
                print '*** Changeset rejection successful.'
            else:
                raise Exception, '*** Changeset rejection failed: Unable to reject changeset.'
        else:
            raise Exception, '*** Invalid syntax: reject_changeset requires 1 argument(id).'
            
    def do_apply_changeset(self, arg, opts=None):
        '''Apply a changeset'''
        if arg:
            changeset_id = arg
            server_id = self.pseudo_raw_input('Enter Server ID: ')
            post = {
                'changeset_id': changeset_id,
                'server_id': server_id,
            }
            r = requests.post('http://%s/api/v1/changeset/apply/' % (self.site),
                                data=json.dumps(post),
                                auth=self.api_auth)
            response = r.json()
            # request_id = response.get('request_id')
            task_id = response.get('task_id')
            # thread_started = response.get('thread_started')
            # if thread_started:
            if task_id:
                # thread_is_alive = True
                task_active = True
                # while thread_is_alive:
                max_tries = 12
                tries = 0
                while True:
                    tries += 1
                    r = requests.get(
                        'http://%s/api/v1/changeset/apply_status/%s/' % (
                            self.site, task_id),
                            auth=self.api_auth)
                    response = r.json()
                    # thread_is_alive = response.get('thread_is_alive')
                    task_active = response.get('task_active')
                    messages = response.get('messages', [])

                    if messages:
                        message = messages[-1]
                        print message['message']

                    if task_active is None:
                        if tries >= max_tries:
                            break
                    else:
                        if not task_active:
                            break
                    time.sleep(10)

                changeset_detail_apply_ids = response.get(
                    'changeset_detail_apply_ids', [])
                print 'Apply Changeset Result Log:'
                for i,apply_id in enumerate(changeset_detail_apply_ids):
                    r = requests.get(
                        'http://%s/api/v1/changeset_detail_apply/%d/' % (
                            self.site, apply_id),
                            auth=self.api_auth)
                    response = r.json()
                    log = response.get('results_log')
                    print '%d. %s' % (i+1, log)
                print
                print '*** Changeset application successful.'
            else:
                raise Exception, '*** Changeset application failed: Unable to apply changeset.'
        else:
            raise Exception, '*** Invalid syntax: apply_changeset requires 1 argument(id).'
