
#!/usr/bin/env bash

# Stop deployment if any command fails
set -o errexit

# Install project dependencies
pip install -r requirements.txt

# Collect Django static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate
