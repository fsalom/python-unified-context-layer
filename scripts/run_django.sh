#!/bin/bash

# Optional argument: $1
# Usage:
#   ./start-django.sh           -> runs the default command
#   ./start-django.sh PRO        -> runs the PRO command

echo "Starting Django server..."

# Set environment variables
export DJANGO_SETTINGS_MODULE=config.settings.staticfiles

python manage.py migrate
if [ "$1" = "PRO" ]; then
    echo "Running in PRO mode..."
    # Command for PRO
    gunicorn config.wsgi:application -k gevent -w 1 -b :8003 --worker-connections=100 --timeout=4000 --reload --log-level=debug --access-logfile=- --error-logfile=- --log-file=-
else
    echo "Running in default (DEV) mode..."
    python manage.py runserver 0.0.0.0:8003
fi
