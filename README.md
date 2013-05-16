Schemanizer Web Application
===========================


Requirements
------------

Aside from the Python packages listed on requirements.txt,
the web application depends on the following to be installed on the system:

Python 2.6 or later
nmap 5.21 or later


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

### Configuration

Copy (schemanizer_root)/schemanizerproj/schemanizerproj/sample.local_settings.py to (schemanizer_root)/schemanizerproj/schemanizerproj/local_settings.py and edit the contents of the new file.  Provided correct values for each setting. The comments for each setting will give you an idea about its purpose.

You will usually need to modify the DATABASES settings and provide values that are needed by the application to connect successfully to a database.  You can also use local_settings.py to override the default settings that are included in (schemanizer_root)/schemanizerproj/schemanizerproj/settings.py.


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

To start the web application's built-in HTTP server:
```
$ cd (schemanizer_root)/schemanizerproj/
$ ./manage.py runserver [optional port number, or ipaddr:port]
```


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

1. New changeset is submitted.
2. Submitted changeset can either be reviewed or rejected.
3. Rejected changesets can be updated again and will have a status similar to newly submitted changeset.
4. Oly reviewed changesets can be approved
5. Reviewed changesets can be rejected.
6. Only approved changesets can be applied.


Custom django-admin Commands
============================

```
$ python manage.py check_changesets_repository
```

Currently outputs to screens information about github repository commits.


Dumping and Restoring Data
==========================

Use the following command to dump data:

```
$ ./manage.py dumpdata -n --format=yaml -e auth.Permission auth sites schemanizer > data.yaml
```

To restore:

```
$ ./manage.py loaddata data.yaml
```

Schema
======

The updated schema is on schemanizerproj/schemanizerproj/data/cdt.sql.


REST API
========

(See: docs/api.md)
