#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Checking if database is empty..."
python -c "
import django
django.setup()
from chat.models import User
if not User.objects.exists():
    from django.core.management import call_command
    call_command('seed_data', force=True)
    print('Fresh database: Seed data successfully loaded!')
else:
    print('Database is not empty: skipping seed_data to protect existing records.')
"

echo "Starting Gunicorn server..."
exec gunicorn chatproject.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 2
