import os

"""
    Handler to select correct settings
"""
if os.environ.get('SECRET_KEY', False):
    from .prod import *
else:
    from .dev import *

try:
    from .custom import *
except ImportError:
    pass
