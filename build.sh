
#!/usr/bin/env bash

# Stop deployment if any command fails
set -o errexit

# Install project dependencies
pip install -r requirements.txt

# Collect Django static files
python manage.py collectstatic --noinput

# Apply database migrations
python manage.py migrate

# Load initial SITF reference data into the deployment database
python manage.py loaddata sitf_initial_data.json

# Create or update the public demonstration account
python manage.py shell -c "
from django.conf import settings;
from django.contrib.auth import get_user_model;
User = get_user_model();
username = settings.DEMO_USER_EMAIL;
user, created = User.objects.get_or_create(
    username=username,
    defaults={'email': username}
);
user.email = username;
user.set_password(settings.DEMO_USER_PASSWORD);
user.is_active = True;
user.is_staff = False;
user.is_superuser = False;
user.save();
print('Demonstration account initialized:', username)
"
