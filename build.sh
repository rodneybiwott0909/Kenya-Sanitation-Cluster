#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
python manage.py collectstatic --noinput
python manage.py migrate
python manage.py load_counties
if [ -f data/county_data.csv ]; then
  python manage.py load_counties --csv data/county_data.csv
fi
python manage.py createsuperuser --noinput || true
