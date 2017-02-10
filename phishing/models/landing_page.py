from django.db.models import CharField, Model, TextField, URLField
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils.translation import ugettext_lazy as _


class LandingPage(Model):
    """
        Landing page created to phish user with custom page

        :param name(CharField): Name of the landing page in mercure interface
        :param domain(URLField): URL of the landing page's domain
        :param html(TextField): Html content of the landing page
    """
    name = CharField(_('Landing page name'), max_length=256, unique=True)
    domain = URLField(_('Domain to use'), blank=True)
    html = TextField(_('HTML source code'))

    def __str__(self):
        """
            Print function for landing page
            :return text: Print the name of the landing page
        """
        return self.name


@receiver(pre_save, sender=LandingPage)
def handler(instance, **kwargs):
    """
        When landing page is saved, replace all the forms to be intercepted
        This function edit the landing_page HTML for redirect all posts data
        to trackers
    """
    from phishing.helpers import intercept_html_post
    instance.html = intercept_html_post(instance.html,
                                        'https://www.google.com')
