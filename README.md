Schemanizer Web Application
===========================


Requirements
------------

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

Start here and login as 'admin' if there are no other users yet.:

```
http://ipaddr:port/
```

###Roles###

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

Dependencies
============

Aside from the Python packages listed on requirements.txt,
the following are used:

Twitter Bootstrap 2.3.1

jQuery 1.9.1

nmap


Schema
======

The updated schema is on schemanizerproj/schemanizerproj/data/cdt.sql.


REST API
========

(See: docs/api.md)
