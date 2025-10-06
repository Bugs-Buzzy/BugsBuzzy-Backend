#!/bin/bash
set -e

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear || {
    echo "Warning: Could not collect static files. Continuing anyway..."
}

echo "Running database migrations..."
python manage.py migrate --noinput

echo "Starting Gunicorn server..."
exec gunicorn --bind 0.0.0.0:8000 --workers 4 core.wsgi:application \
    --log-level info --access-logfile - --error-logfile - --timeout 120 --preload
