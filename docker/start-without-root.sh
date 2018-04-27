#!/usr/bin/env sh

# Prepare database
python manage.py makemigrations
python manage.py migrate

# Run web server
exec gunicorn mercure.wsgi:application --bind 0.0.0.0:8000 --workers 3 --access-logfile -
