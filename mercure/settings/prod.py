import os
from django.conf import global_settings

from .base import *

# django config
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = 'DEBUG' in os.environ

# mercure config
HOSTNAME = os.environ.get('URL', 'http://localhost')

# email config
EMAIL_BACKEND = os.environ.get('EMAIL_BACKEND', global_settings.EMAIL_BACKEND)
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'phishing@example.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'P@SSWORD')
EMAIL_PORT = os.environ.get('EMAIL_PORT', 587)
EMAIL_SSL_CERTFILE = os.environ.get('EMAIL_SSL_KEYFILE', None)
EMAIL_SSL_KEYFILE = os.environ.get('EMAIL_SSL_KEYFILE', None)
EMAIL_TIMEOUT = os.environ.get('EMAIL_TIMEOUT', None)

DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)
SERVER_EMAIL = os.environ.get('SERVER_EMAIL', EMAIL_HOST_USER)

EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'False') \
    .lower() in ['true', '1', 't', 'y', 'yes']
EMAIL_USE_SSL = os.environ.get('EMAIL_USE_SSL', 'False') \
    .lower() in ['true', '1', 't', 'y', 'yes']

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_PORT', 'tcp://redis:6379'),
    },
}

RQ_QUEUES = {
    'default': {
        'URL': os.environ.get('REDIS_PORT', 'tcp://redis:6379'),
    },
}

# sentry.io (send error to platform)
if 'SENTRY_DSN' in os.environ:
    import raven

    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)
    RAVEN_CONFIG = {
        'dsn': os.environ['SENTRY_DSN'],
        # If you are using git, you can also automatically configure the
        # release based on the git info.
        'release': raven.fetch_git_sha(os.path.dirname(os.pardir)),
    }

# security (forcebrute)
INSTALLED_APPS += ('axes',)
AXES_LOCK_OUT_AT_FAILURE = os.environ.get('AXES_LOCK_OUT_AT_FAILURE', True)
AXES_COOLOFF_TIME = os.environ.get('AXES_COOLOFF_TIME', 0.8333)  # 5 minutes

# if protection active => send alert to sentry.io
if 'SENTRY_DSN' in os.environ and AXES_LOCK_OUT_AT_FAILURE:
    import raven
    import logging
    from raven.contrib.django.raven_compat.handlers import SentryHandler

    logger = logging.getLogger('axes.watch_login')
    logger.addHandler(SentryHandler(level=logging.WARN))
    logger.addHandler(logging.StreamHandler())
