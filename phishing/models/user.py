from django.contrib.auth.models import AbstractUser
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from phishing.signals import make_menu


class User(AbstractUser):
    """
        Mercure's user management
    """
    def __str__(self):
        return self.username

    def get_menu(self):
        """
            Get user menu dict link

            :return urls: Return urls' dictionnary(name/url/permissions)
        """
        urls = [
            {
                'name': _('Campaigns'),
                'url': reverse('campaign_list'),
                'glyphicon': 'send',
            },
            {
                'type': 'separator',
            },
            {
                'name': _('Email Templates'),
                'url': reverse('email_template_list'),
                'permission_required': 'phishing.view_emailtemplate',
                'glyphicon': 'envelope',
            },
            {
                'name': _('Attachments'),
                'url': reverse('attachment_list'),
                'permission_required': 'phishing.view.attachment',
                'glyphicon': 'download-alt',
            },
            {
                'name': _('Landing page'),
                'url': reverse('landing_page_list'),
                'permission_required': 'view_landingpage',
                'glyphicon': 'edit',
            },
            {
                'type': 'separator',
            },
            {
                'name': _('Targets'),
                'url': reverse('target_group_list'),
                'permission_required': 'phishing.view_targetgroup',
                'glyphicon': 'screenshot',
            },
        ]

        # call modules handler
        make_menu.send(sender=User, urls=urls)

        # has permission ?
        for url in urls.copy():
            perm = url.get('permission_required', None)
            if perm and not self.has_perm(perm):
                urls.remove(url)

        return urls
