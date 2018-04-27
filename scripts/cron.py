# connect to django context
import os
import sys
print(sys.version)
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mercure.settings')
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()


# script code
from phishing.models import Campaign

# send all unsendend campaign (with send_at passed)
Campaign.send_all()
