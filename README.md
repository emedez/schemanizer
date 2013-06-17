Schemanizer Web Application
===========================


Requirements
------------

Aside from the Python packages listed on requirements.txt,
the web application depends on the following to be installed on the system:

Python 2.6 or later
Mercurial
RabbitMQ
nmap 5.21 or later


### Installing Mercurial

For Ubuntu:

$ sudo apt-get install mercurial


### Installing RabbitMQ

Schemanizer web application uses Celery with RabbitMQ as mesage transport to create job queues.
To install RabbitMQ in Ubuntu (see http://www.rabbitmq.com/download.html for other OS):

* Add the following line to your etc/apt/sources.list:

```
deb http://www.rabbitmq.com/debian/ testing main
```

* Add rabbitmq public key to trusted key list using apt-key:

```
$ wget http://www.rabbitmq.com/rabbitmq-signing-key-public.asc
$ sudo apt-key add rabbitmq-signing-key-public.asc
```

* Run sudo apt-get update

* Install packages as usual; for instance,

```
$ sudo apt-get install rabbitmq-server
```


#### Starting/Stopping the RabbitMQ server

To start the server:

```
$ sudo invoke-rc.d rabbitmq-server start
```

To stop the server:

```
$ sudo rabbitmqctl stop
```
When the server is running, you can continue reading Setting up RabbitMQ.


#### Setting up RabbitMQ

To use celery we need to create a RabbitMQ user, a virtual host and allow that user access to that virtual host.
In the following example, user 'sandbox', password 'sandbox', hostname 'myhostname' are used:
```
$ sudo rabbitmqctl add_user sandbox sandbox
$ sudo rabbitmqctl add_vhost myhostname
$ sudo rabbitmqctl set_permissions -p myhostname sandbox ".*" ".*" ".*"
```


### virtualenv

It is recommended to install the the web application and its requirements in an isolated Python environments.
virtualenv is a tool that can create such environments.

To install virtualenv:
```
$ pip install virtualenv
```

To create a virtual environment:
```
$ virtualenv venv --no-site-packages
```

To begin using the virtual environment, it needs to be activated:
```
$ source venv/bin/activate
```
At this point, you can begin installing any new modules without affecting the system default Python or other virtual environments.

If you are done working in the virtual environment, you can deactivate it:
```
$ deactivate
```


### Installing Packages Listed On requirements.txt

The requirements.txt file contains the required components for the
web applicaton.

To install the requirements, run the following inside a virtual environment:
```
$ pip install -r requirements.txt
```

Note:
    stable-requirements.txt is also provided and can be used instead of requirements.txt if newer versions of packages causes issues.


Setup
-----


### Settings

Copy (schemanizer_root)/schemanizerproj/schemanizerproj/sample.local_settings.py to (schemanizer_root)/schemanizerproj/schemanizerproj/local_settings.py and edit the contents of the new file.  Provided correct values for each setting. You can also use local_settings.py to override the default settings that are included in (schemanizer_root)/schemanizerproj/schemanizerproj/settings.py.


#### Database Settings

To use a particular database, specifiy the connection details in the 'default' key of DATABASES.
```
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',   # other supported backends: postgresql_psycopg2, sqlite3, oracle
            'NAME': 'dbname',                       # database name or path to database file if using sqlite3
            'USER': 'dbuser',                       # database user, unused with sqlite3
            'PASSWORD': 'dbpassword',               # database password, unused with sqlite3
            'HOST': '',                             # set empty string for localhost
            'PORT': ''                              # set empty string for default
        }
    }
```


#### Email Settings

A mail delivery system is needed to enable email notifications.
Mail is sent using the SMTP host and port specified in the EMAIL_HOST and
EMAIL_PORT settings.  The EMAIL_HOST_USER and EMAIL_HOST_PASSWORD settings,
if set, are used to authenticate to the SMTP server, and the EMAIL_USE_TLS
setting controls whether a secure connection is used.
```
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'test@example.com'
EMAIL_HOST_PASSWORD = 'pass'
EMAIL_USE_TLS = True
```

Default email sender.
```
DEFAULT_FROM_EMAIL = 'Schemanizer <schemanizer@example.com>'
```

Set to True to disable sending of Schemanizer emails.
```
DISABLE_SEND_MAIL = False
```


#### Changeset Review Settings

When reviewing changesets, the application creates and starts an EC2 instance based on configured image. This EC2 instance should have MySQL pre-installed.
The following settings needs to have the correct values to successful launch an EC2 instance:

AWS Credentials
```
AWS_ACCESS_KEY_ID = None
AWS_SECRET_ACCESS_KEY = None
```

The name of the region to connect to.
```
AWS_REGION = 'ap-southeast-1'
```

The ID of the image to run.
```
AWS_AMI_ID = 'ami-4edb971c'
```

The name of the key pair with which to launch instances.
```
AWS_KEY_NAME = 'tools-sqlcanon1-sg-key'
```

The names (list of strings) of the security groups with which to associate instance.
```
AWS_SECURITY_GROUPS = ['quicklaunch-1']
```

The type of instance to run,
choices are: t1.micro, m1.small, m1.medium, m1.large, m1.xlarge, c1.medium, c1.xlarge,
m2.xlarge, m2.2xlarge, m2.4xlarge, cc1.4xlarge, cg1.4xlarge, cc2.8xlarge
```
AWS_INSTANCE_TYPE = 'm1.small'
```


#### MySQL Server Settings for Changeset Operations

MySQL host and port. If AWS_MYSQL_HOST is None, the EC2 instance host name is used.
AWS_MYSQL_PORT, AWS_MYSQL_USER and AWS_MYSQL_PASSWORD are also used in changeset apply operations.
```
AWS_MYSQL_HOST = None
AWS_MYSQL_PORT = None
AWS_MYSQL_USER = 'sandbox'
AWS_MYSQL_PASSWORD = 'sandbox'
```

When an EC2 instance is launched, it needs some time before it can be utilized.
This setting value is the number of seconds to wait for EC2 instance to start before accessing it.
```
AWS_EC2_INSTANCE_START_WAIT = 60
```

Number of seconds to wait before trying to connect to MySQL server. This is to give time for it to start completely.
```
AWS_MYSQL_START_WAIT = 60
```

#### django-celery Settings

Broker URL in the form: transport://userid:password@hostname:port/virtual_host
Only the scheme part (transport://) is required, the rest is optional, and
defaults to the specific transports default values
```
# The following is the broker URL for RabbitMQ
BROKER_URL = 'amqp://sandbox:sandbox@localhost:5672/myhostname'
```


#### Github Settings

The following settings are used when loading changesets from a Github repository.

Github repo commits URL in the following format: https://api.github.com/repos/owner/repo/commits
```
CHANGESET_REPO_URL = https://api.github.com/repos/user_name/repository_name/commits
```

The authorization token used when calling Github APIs.
To create a token, POST to https://api.github.com/authorizations with note and scopes values in the data hash,
for example:
    $ curl -u username -d '{"scopes":["repo"],"note":"Schemanizer repo access token."}' https://api.github.com/authorizations
```
AUTHORIZATION_TOKEN = None
```

The directory, in the repository, to look for changesets.
```
CHANGESET_PATH = None
```

#### Site Information Settings
The values found here are automatically used to update site information
whenever a management command syncdb is executed.
```
SITE_NAME = 'Schemanizer'
SITE_DOMAIN = '127.0.0.1:8000'
```


#### MySQL Server Discover Settings

Schemanizer utilizes nmap to perform MySQL server discovery.
Specify hosts and ports to scan using nmap.
```
NMAP_HOSTS = '192.168.43.0/24'
NMAP_PORTS = '3300-3310'
```


### Database Initialization

To prepare the database for use:
```
$ cd (schemanizer_root)/schemanizerproj
$ mysql -u user -p dbname < ./data/cdt.sql
$ ./schemanizer_init.sh
```

_**dbname**_ should be the same as the database name that you had set in your local_settings.py.

At this point user 'admin' now exists with password 'admin'.


Running
-------

To use the schemanizer application, the following processes needs to be launched:

* Django HTTP server
* Celery worker - for processing tasks
* Celery cam - updates database with status of tasks

These processes can be ran inside a terminal multiplexer such as screen for convenience.
To run these processes inside screen, following the following steps
(don't forget to activate virtual environment in each window):

Start screen:
```
$ screen
```

Start Django HTTP server:
```
$ cd (schemanizer_root)/schemanizerproj/
$ ./manage.py runserver [optional port number, or ipaddr:port]
```

Press Ctrl-A then c to create a new window.

Start Celery worker to process job queues:
```
$ ./manage.py celery worker -E --loglevel=DEBUG
```
Notes:
-E option needs to be present to enable capturing of tasks events with Celery cam.
--loglevel is optional


Press Ctrl-A then c to create another window.

Start Celery cam to record task statuses.
```
$ ./manage.py celerycam
```

Switching between windows:
Ctrl-A n    next window
Ctrl-A p    previous window
Ctrl-A d    detach

To list screens:
```
$ screen -ls
```

To reconnect to screen:
```
$ screen -r [host.tty]
```

To detach and logout remote, and re-attach at the current host:
```
$ screen -D -R
```

At this point the Schemanizer application is now ready to be used.


Usage
-----

When the application is freshly installed, only one user exists - admin, with a default password of admin.
Start here and login as 'admin' if there are no other users yet.:
```
http://ipaddr:port/
```
In the next examples, localhost:8000 will be used in place of ipadd:port.


### Roles

1. **developer** - Users with this role have the following permissions:
    * submit changesets
    * edit/delete changesets that were not yet approved
    * view changesets
    * view applied changeset results
2. **dba** - In addition to the permissions granted for developers, dbas have
the following permissions:
    * review changeset
    * approve/reject changeset
3. **admin** - Admins can do everything that a developer or dba can
plus add/edit/delete users.


### Users

Only admin users can create, update or delete users.
Click on the 'Users' link from the menu bar or browse the
URL http://localhost:8000/schemanizer/user/list/ to go to a page
that provides links for creating, updating and deleting users.


### Environments

Environment refers to the name of environment for the server.
Predefined are dev, test, and prod. You can create, update or delete
environments at the URL http://localhost:8000/schemanizer/environments/list/
or click Data -> Environments.


### Servers

Server refers to the to collection of information about a MySQL server.
Browse the URL http://localhost:8000/schemanizer/server/list/ or
click Data -> Servers to go to server list page.
In the server list page, you will be able to create, update or delete entries
about a MySQL server.

Browsing URL http://localhost:8000/schemanizer/server/discover/ or clicking
Discover servers link will scan hosts in a local area network for
MySQL server installations.
This feature depends on the following Django settings:

NMAP_HOSTS - hosts to scan, for example: '192.168.1.103/24'
NMAP_PORTS - ports to scan, for example: '3300-3310'


### Database Schemas and Schema Versions

On the server list page, clicking on Create schema version link enables user to
create a schema version by selecting a schema name from the list.
Schema name is then saved as a Database Schema entry (a new entry will be created)
if the schema name does not exist yet. New schema version entry is also created
if no entry with the same checksum and schema name exists yet.

To view database schema list, click on Data -> Database Schemas.
To view schema version list, click on Data -> Schema Versions.


### Changesets

Clicking on the Data -> Changesets will show a list of changesets.
The workflow for the changesets are the following:

1. New changeset is submitted (changeset review is automatically scheduled to start as soon as possible).
2. Submitted changeset can either be reviewed or rejected.
3. Rejected changesets can be updated again and will have a status similar to newly submitted changeset.
4. Oly reviewed changesets can be approved
5. Reviewed changesets can be rejected.
6. Only approved changesets can be applied.


Custom django-admin Commands
============================

### check_changesets_repository

Processes changesets stored in commits in a Github repository.
Files with status equal to 'added' are treated as changeset submission.
File with status equal to 'modified', but has never been processed, is also treated as changeset submission, otherwise it updates existing changeset.

```
Usage: python manage.py check_changesets_repository [options]

Options:
  -v VERBOSITY, --verbosity=VERBOSITY
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
  --settings=SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
  --pythonpath=PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Print traceback on exception
  --since=SINCE         ISO 8601 Date, for example, 2011-04-14T16:00:49Z. Only
                        commits after this date will be processed.
  --since-hours=SINCE_HOURS
                        Only commits after the date/time SINCE_HOURS ago will
                        be processed. If not None, this overrides the value of
                        --since option
  --version             show program's version number and exit
  -h, --help            show this help message and exit
```

Dumping and Restoring Data
==========================

Use the following command to dump data:

```
$ ./manage.py dumpdata --indent=4 -n -e auth.Permission auth sites schemanizer > data.json
```

To restore:

```
$ ./manage.py loaddata data.json
```

Schema
======

The updated schema is on schemanizerproj/schemanizerproj/data/cdt.sql.


REST API
========

(See: docs/api.md)

Schemanizer CLI
===============

(See: docs/cli.md)
