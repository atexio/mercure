"""
WSGI config for mercure project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mercure.settings")

# In docker SECRET_KEY a required
if not os.environ.get('SECRET_KEY', None) and os.path.exists('/proc/1/cgroup'):
    with open('/proc/1/cgroup', 'rt') as f:
        if 'docker' in f.read():
            raise EnvironmentError(
                'In docker the SECRET_KEY environment variable is required')

application = get_wsgi_application()
