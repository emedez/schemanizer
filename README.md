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

Edit the contents of local_settings.py and set the correct values.

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

Run Server
----------

Do the following:
```
$ ./manage.py runserver
```


Dumping Data
============

./manage.py dumpdata -n --format=yaml auth.User auth.Group sites schemanizer > data.yaml


Dependencies
============

Aside from the Python packages listed on requirements.txt,
the following are used:

Twitter Bootstrap 2.3.1

jQuery 1.9.1


Schema Changes
==============

The updated schema is on schemanizerproj/schemanizerproj/data/cdt.sql.

The following are the modifications:

*Table: users*

From:
```
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `role_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

To:
```
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) DEFAULT NULL,
  `email` varchar(255) DEFAULT NULL,
  `role_id` int(11) DEFAULT NULL,
  `auth_user_id` int(11) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
```

Notes:
Added auth_user_id, to take advantage of Django framework's builtin User object.
