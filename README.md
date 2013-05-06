Installation and Running
========================

Setup
-----

Install requirements via pip.

```
$ pip install -r requirements.txt
```

Set Local Settings
------------------

Copy schemanizerproj/schemanizerproj/local_settings.py.sample to schemanizerproj/schemanizerproj/local_settings.py

Edit the contents of local_settings.py and set the correct values for settings.

Initial Data
------------

Do the following:

```
$ mysql -u user -p dbname < schemanizerproj/data/cdt.sql
$ cd schemanizerproj
$ ./manage.py syncdb --noinput
$ ./manage.py migrate --fake
$ ./manage.py loaddata ./fixtures/initial_data.yaml
```

_**dbname**_ should be the same as the database name that you had set in your local_settings.py.

At this point user 'admin' now exists with password 'admin'.


Run Server
----------

Do the following:

```
$ ./manage.py runserver [ipaddr:port]
```

If ipaddr:port is not specified the following default is used:
localhost:8000


Update Site Domain Name
-----------------------

During data initialization, the site information specified in
settings.SITE_NAME and settings.SITE_DOMAIN are automatically saved during data
initialization. If this needs to be changed later, browse the following URL,
login as admin, edit the only record and update
the domain name to the correct address and the optional port number.
This value is used for building absolute URL paths such as email functions
which usually do not have access to web requests data.

```
http://ipaddr:port/admin/sites/site/
```

Logout after updating site domain name.


Web App Usage
-------------

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


Unit Testing
============

To run the tests:

```
$ ./manage.py test schemanizer
```


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


Schema
======

The updated schema is on schemanizerproj/schemanizerproj/data/cdt.sql.

