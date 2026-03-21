#!/usr/bin/env bash
# Build script for Render deployment
set -o errexit

echo "── Installing dependencies ──"
pip install -r requirements.txt

echo "── Collecting static files ──"
python manage.py collectstatic --noinput

echo "── Running migrations ──"
python manage.py migrate

echo "── Creating/updating default users ──"
python manage.py setup_users

echo "── Build complete ──"
