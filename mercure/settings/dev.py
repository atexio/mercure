from .base import *

DEBUG = True


# Dev settings / Contain email parameters
EMAIL_HOST = 'smtp.mandrillapp.com'
EMAIL_PORT = '587'
EMAIL_HOST_USER = 'phishing@example.com'
EMAIL_HOST_PASSWORD = 'P@SSWORD'
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

HOSTNAME = 'http://localhost'


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
