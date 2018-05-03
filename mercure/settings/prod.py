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

# Send error to sentry.io
if 'SENTRY_DSN' in os.environ:
    import raven

    INSTALLED_APPS += ('raven.contrib.django.raven_compat',)
    RAVEN_CONFIG = {
        'dsn': os.environ['SENTRY_DSN'],
    }

# Forcebrute account protection
AXE_DISABLED = os.environ.get('AXE_DISABLED', 'False') \
    .lower() in ['true', '1', 't', 'y', 'yes']
if not AXE_DISABLED:
    INSTALLED_APPS += ('axes',)
    AXES_LOCK_OUT_AT_FAILURE = os.environ.get('AXES_LOCK_OUT_AT_FAILURE', True)
    AXES_COOLOFF_TIME = os.environ.get('AXES_COOLOFF_TIME', 0.8333)  # 5 min

    # Init defaut axes_cache if default django cache is used
    AXES_CACHE = 'axes_cache'
    if 'default' not in CACHES or CACHES.get('default', {}).get('BACKEND', '')\
            .endswith('LocMemCache'):
        CACHES['axes_cache'] = {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }

# if forcebrute protection is active: send alert to sentry.io
if 'SENTRY_DSN' in os.environ and not AXE_DISABLED:
    import raven
    import logging
    from raven.contrib.django.raven_compat.handlers import SentryHandler

    logger = logging.getLogger('axes.watch_login')
    logger.addHandler(SentryHandler(level=logging.WARN))
    logger.addHandler(logging.StreamHandler())
