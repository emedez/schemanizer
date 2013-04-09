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
$ mysql -u <user> -p <dbname> < schemanizerproj/data/cdt.sql

$ cd schemanizerproj

$ ./manage.py syncdb --noinput
$ ./manage.py migrate --fake
$ ./manage.py loaddata schemanizer/fixtures/initial_data.yaml
```

&lt;dbname&gt; should be the same as the database name that you had set in your local_settings.py.

At this point user 'admin' now exists with password 'admin'.


Run Server
----------

Do the following:
```
$ ./manage.py runserver
```


Dumping Data
============

```
./manage.py dumpdata -n --format=yaml auth.User auth.Group sites schemanizer > data.yaml
```

Dependencies
============

Aside from the Python packages listed on requirements.txt,
the following are used:

Twitter Bootstrap 2.3.1

jQuery 1.9.1


Schema Changes
==============

The updated schema is on schemanizerproj/schemanizerproj/data/cdt.sql.

