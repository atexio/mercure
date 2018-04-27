"""Django model edit"""
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_migrate

from .attachment import Attachment
from .campaign import Campaign, CampaignTargetGroups
from .email_template import EmailTemplate
from .landing_page import LandingPage
from .target import Target, TargetGroup
from .tracker import Tracker, TrackerInfos
from .user import User

__all__ = [
    'Attachment', 'Campaign', 'CampaignTargetGroups', 'EmailTemplate',
    'LandingPage', 'Target', 'TargetGroup', 'Tracker', 'TrackerInfos', 'User'
]


# add django view model permission
def add_view_permissions(sender, **kwargs):
    """
    This syncdb hooks takes care of adding a view permission too all our
    content types.
    """
    # for each of our content types
    for content_type in ContentType.objects.all():
        # build our permission slug
        codename = 'view_%s' % content_type.model

        # if it doesn't exist..
        if not Permission.objects.filter(content_type=content_type,
                                         codename=codename):
            # add it
            Permission.objects.create(content_type=content_type,
                                      codename=codename,
                                      name='Can view %s' % content_type.name)


# check for all our view permissions after a syncdb
post_migrate.connect(add_view_permissions)
