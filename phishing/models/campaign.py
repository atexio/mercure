from django.db.models import BooleanField, CharField, DateTimeField, \
    ForeignKey, ManyToManyField, Model, CASCADE
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _


class Campaign(Model):
    """
        Send phishing campaign.

        :param created_at(DateTimeField): Date format to know when the campaign
                                            be created
        :param email_template(ForeignKey): Link to :func:`email template class
                                <phishing.models.email_tempalte.EmailTemplate>`
        :param name(CharField): Name of the campaign in mercure interface
        :param target_groups(ManyToManyField): Link to :func:`target group
                                class  <phishing.models.target.TargetGroup>`
        :param send_at(DateTimeFIeld): Date format to know when the campaign
                                        will be launched.
        :param dropper_unique(BooleanField): Boolean to know if the dropper is
                                            unique
        :param minimize_url(BooleanField): Boolean to set if url need to be
                                            minimized
        :param smtp_host(CharField): (optional) Custom SMTP host
        :param smtp_username(CharField): (optional) Custom SMTP username
        :param smtp_password(CharField): (optional) Custom SMTP password
        :param smtp_use_ssl(BooleanField): (optional) Boolean - Custom SMTP use
    """

    # global infos
    created_at = DateTimeField(auto_now_add=True)
    email_template = ForeignKey('EmailTemplate', related_name='campaigns',
                                on_delete=CASCADE)
    name = CharField(_('Campaign name'), max_length=128)
    target_groups = ManyToManyField('TargetGroup', related_name='campaigns')
    send_at = DateTimeField(default=now)

    # app config
    minimize_url = BooleanField(_('Minimize url in email'), default=False)

    # optional config
    smtp_host = CharField(_('Custom SMTP hostname'), max_length=128,
                          blank=True)
    smtp_username = CharField(_('Custom SMTP username'), max_length=128,
                              blank=True)
    smtp_password = CharField(_('Custom SMTP password'), max_length=256,
                              blank=True)
    smtp_use_ssl = BooleanField(_('Custom SMTP server use SSL'), default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        """
            Print function for campaign
            :return text: Print the name of the campaign
        """
        return self.name

    @property
    def is_launched(self):
        return self.trackers.count() > 0

# TODO: sortir la conf smtp => faire un model
#
#  class SmtpServer(Model):
#   host = CharField(_('Custom SMTP hostname'), max_length=128, blank=True)
#   username = CharField(_('Custom SMTP username'),max_length=128, blank=True)
#   password = CharField(_('Custom SMTP password'),max_length=256, blank=True)
#   use_ssl = BooleanField(_('Custom SMTP server use SSL'), blank=True)
#
# TODO: bouton de test de campagne
