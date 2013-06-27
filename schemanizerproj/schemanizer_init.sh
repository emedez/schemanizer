#!/usr/bin/env bash
python manage.py syncdb --noinput
python manage.py migrate --fake events
python manage.py migrate --fake users
python manage.py migrate --fake servers
python manage.py migrate --fake schemaversions
python manage.py migrate --fake schemanizer
python manage.py migrate tastypie
python manage.py migrate djcelery
python manage.py loaddata ./fixtures/initial_data.json
