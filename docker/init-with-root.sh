#!/usr/bin/env sh


# Prepare docker module migration
if [ ! -f /code/phishing/migrations/__init__.py ]; then
    # First boot on docker volume
    touch /code/phishing/migrations/__init__.py
fi


# Create vulume directory
mkdir -p /code/database
mkdir -p /code/media


# Apply user right for docker volumes
chown -R mercure:mercure /code/database
chown -R mercure:mercure /code/media
chown -R mercure:mercure /code/phishing/migrations


# Save project env variable (for cron job)
printenv >> /etc/environment
