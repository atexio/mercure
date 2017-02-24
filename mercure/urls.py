"""
    mercure URL Configuration

    The `urlpatterns` list routes URLs to views. For more information, see :
        https://docs.djangoproject.com/en/1.9/topics/http/urls/

    Examples

    Function views
        1. Add an import:  from my_app import views
        2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
    Class-based views
        1. Add an import:  from other_app.views import Home
        2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
    Including another URLconf
        1. Import the include() function:
        from django.conf.urls import url, include
        2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
import os
import re

from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.views.decorators.csrf import csrf_exempt
from django.views.static import serve


urlpatterns = i18n_patterns(
    url(r'^', include('phishing.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    url(r'^admin/', admin.site.urls),
)


# serve static files (for prod docker) ?
DONT_SERVES_STATIC_FILE = os.environ.get('DONT_SERVES_STATIC_FILE', 'False') \
    .lower() in ['true', '1', 't', 'y', 'yes']
if not DONT_SERVES_STATIC_FILE:
    urlpatterns += url(
        r'^%s(?P<path>.*)$' % re.escape(settings.STATIC_URL.lstrip('/')),
        csrf_exempt(serve), kwargs={'document_root': settings.STATIC_ROOT}
    ),
