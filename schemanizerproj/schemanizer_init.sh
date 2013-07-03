#!/usr/bin/env bash
python manage.py syncdb --noinput --all
python manage.py migrate --fake
python manage.py loaddata ./fixtures/initial_data.json
