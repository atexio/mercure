from django.db.models import BooleanField, CASCADE, CharField, ForeignKey, \
    Model, TextField
from django.db.models import ManyToManyField
from django.utils.translation import ugettext_lazy as _


class EmailTemplate(Model):
    """
        Email template send in campaign.

        :param name(CharField): Name of the email template in mercure interface
        :param email_subject(CharField): Text of email's subject
        :param from_email(CharField): Text of email's sender
        :param has_open_tracker(BooleanField): Tracker to get if target open
                                                the email
        :param text_content(TextField): Text content of the email
        :param html_content(TextField): Html content of the email
        :param landing_page(ForeignKey): Link to :func:`landing page class
                                    <phishing.models.landing_page.LandingPage>`
        :param attachments(ManyToManyField): Link to :func:`attachments class
                                    <phishing.models.attachments.Attachments>`
    """
    name = CharField(_('Email template name'), unique=True, max_length=128)
    email_subject = CharField(_('subject'), max_length=128)
    from_email = CharField(_('from'), max_length=128)
    has_open_tracker = BooleanField(_('Add open email tracker'), default=True)
    text_content = TextField(_('Email template content (text version)'))
    html_content = TextField(_('Email template content (HTML version)'),
                             blank=True)

    landing_page = ForeignKey('LandingPage', on_delete=CASCADE, blank=True,
                              null=True, related_name='email_template')
    attachments = ManyToManyField('Attachment',
                                  related_name='email_attachment',
                                  blank=True)

    def __str__(self):
        """
            Print function for email template
            :return text: Print the name of the email template
        """
        return self.name
