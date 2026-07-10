#!/bin/sh

# Exit immediately if a command exits with a non-zero status
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Checking if database is empty..."
python -c "
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chatproject.settings')
import django
django.setup()
from chat.models import User
if not User.objects.exists():
    from django.core.management import call_command
    call_command('seed_data', force=True)
    print('Fresh database: Seed data successfully loaded!')
else:
    print('Database is not empty: skipping seed_data to protect existing records.')

# Always ensure the partners table is seeded correctly on start
from chat.models import Partner
if Partner.objects.count() < 56:
    print('Partners list is incomplete or empty in the database. Seeding partners...')
    try:
        from chat.management.commands.seed_data import PARTNERS_LIST
        Partner.objects.all().delete()
        for name, ref, c1, c2, zone_val, p_type, meteo_val in PARTNERS_LIST:
            Partner.objects.create(
                name=name,
                ref=ref,
                contact_1=c1,
                contact_2=c2,
                zone=zone_val,
                property_type=p_type,
                meteo=meteo_val
            )
        print('Successfully seeded all 56 partners!')
    except Exception as e:
        print('Error seeding partners:', e)
"

echo "Starting Gunicorn server..."
exec gunicorn chatproject.wsgi:application --bind 0.0.0.0:8000 --workers 3 --threads 2
