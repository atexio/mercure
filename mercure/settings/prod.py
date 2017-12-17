import os

from .base import *

# django config
SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = 'DEBUG' in os.environ

# mercure config
HOSTNAME = os.environ.get('URL', 'http://localhost')

# email config
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'localhost')
EMAIL_PORT = os.environ.get('EMAIL_PORT', '587')
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'phishing@example.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'P@SSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER

CACHES = {
    'default': {
        'BACKEND': 'redis_cache.cache.RedisCache',
        'LOCATION': '%s:%s' % (os.environ.get('REDIS_HOST', 'redis'),
                               os.environ.get('REDIS_PORT', '6379')),
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
