import copy

import traceback
from django.core.mail import EmailMultiAlternatives
from django.core.mail.backends.smtp import EmailBackend
from django.db.models import BooleanField, CharField, DateTimeField, \
    ForeignKey, ManyToManyField, Model, CASCADE
from django.template.loader import render_to_string
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

from mercure.settings import HOSTNAME
from phishing.helpers import replace_template_vars
from phishing.signals import send_email
from phishing.strings import TRACKER_ATTACHMENT_EXECUTED, TRACKER_EMAIL_OPEN, \
    TRACKER_LANDING_PAGE_OPEN, POST_TRACKER_ID, TRACKER_LANDING_PAGE_POST, \
    TRACKER_EMAIL_SEND


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
    target_groups = ManyToManyField('TargetGroup', related_name='campaigns',
                                    through='CampaignTargetGroups')
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

    def get_smtp_connection(self):
        """Get SMTP connection.
        :return: SMTP connection
        """
        if not self.smtp_host:
            return None

        options = {
            'use_ssl': self.smtp_use_ssl
        }

        # add host / port infos
        if ':' in self.smtp_host:
            host, port = self.smtp_host.split(':')
            options['host'] = host
            options['port'] = int(port)

        else:
            options['host'] = self.smtp_host

        # add cred infos
        if self.smtp_username:
            options['username'] = self.smtp_username

        if self.smtp_password:
            options['password'] = self.smtp_password

        return EmailBackend(**options)

    @property
    def is_launched(self):
        return self.trackers.count() > 0

    def send(self):
        # ignore if sending date are not passed
        if self.send_at > now():
            return False

        # ignore if not targets group
        if not self.campaigntargetgroups_set.count():
            return False

        # all target group send
        has_error = False
        for target_group_link in self.campaigntargetgroups_set.all():
            if not target_group_link.send():
                has_error = True

        return not has_error

    @classmethod
    def send_all(cls):
        has_error = False

        # search unsended campagn
        query = cls.objects.filter(
            send_at__lte=now(),  # date passed (or equal)
            campaigntargetgroups__sended_at__isnull=True,  # not send
            campaigntargetgroups__isnull=False  # has target group
        )

        for campaign in query.all():
            if not campaign.send():
                has_error = True

        return not has_error

    def target_groups_add(self, target_group):
        # create method for fix 'campaign.target_groups.add'
        # Django message error:
        # AttributeError: Cannot use add() on a ManyToManyField which
        # specifies an intermediary model. Use phishing.CampaignTargetGroups's
        # Manager instead.
        return CampaignTargetGroups.objects.create(campaign=self,
                                                   target_group=target_group)


class CampaignTargetGroups(Model):
    """Many to many link"""
    campaign = ForeignKey(Campaign, on_delete=CASCADE)
    target_group = ForeignKey('TargetGroup', on_delete=CASCADE)
    sended_at = DateTimeField(blank=True, null=True)

    def __str__(self):
        state = 'send' if self.sended_at else 'not send'
        return '[%s] "%s" in "%s"' % (state, self.target_group, self.campaign)

    def send(self):
        """Send emails to targets groups"""
        # targets group has target ?
        if not self.target_group.targets.count():
            return False

        from phishing.models import Tracker

        # prepare vars
        has_error = False
        self._cache_smtp_connection = self.campaign.get_smtp_connection()

        # get all email already send for this campagn
        email_already_received = [
            t.target.email for t in
            Tracker.objects.filter(campaign_id=self.campaign_id,
                                   key=TRACKER_EMAIL_SEND)
        ]

        # iterate of all target
        for target in self.target_group.targets.all():
            # ignore already send email (target in multiple group for example)
            if target.email in email_already_received:
                continue
            email_already_received.append(target.email)

            # prepare and send email to target
            try:
                mail = self._make_email(target)
                mail.send(fail_silently=False)
                self._add_tracker(TRACKER_EMAIL_SEND, 'success')

            except Exception:
                has_error = True
                self._add_tracker(
                    TRACKER_EMAIL_SEND, 'fail', traceback.format_exc()
                )

        # flag target groups link to sended
        self.sended_at = now()
        self.save()

        return not has_error

    def _add_tracker(self, key, value, infos=None):
        """helper for create tracker"""
        from phishing.models import Tracker

        kwargs = {
            'key': key,
            'campaign_id': self.campaign_id,
            'target': self._cache_current_target,
            'value': value,
        }

        if infos:
            kwargs['infos'] = str(infos)

        return Tracker.objects.create(**kwargs)

    def _make_email(self, target):
        """Prepare email for target"""
        # get values
        email_template = self.campaign.email_template
        landing_page = email_template.landing_page
        target_email = copy.deepcopy(email_template)
        smtp_connection = self._cache_smtp_connection

        # update cache (for helpers class function)
        self._cache_current_target = target

        # prepare / build attachments files
        attachments = []
        for attachment in email_template.attachments.all():
            # build custom attachment
            if attachment.buildable:
                attachment_file = attachment.build(self._add_tracker(
                    TRACKER_ATTACHMENT_EXECUTED,
                    '%s: not executed' % attachment.name,
                    0
                ))

            # static file on attachment
            else:
                attachment_file = attachment.file

            attachments.append({
                'filename': attachment.attachment_name,
                'content': attachment_file.read()
            })

        # Signal for external app
        send_email.send(
            attachments=attachments, campaign=self.campaign,
            email_template=target_email, sender=self,
            target=target, smtp_connection=smtp_connection
        )

        # Add email open tracker in email
        if email_template.has_open_tracker:
            # convert txt to html if empty
            target_email.html_content = self._make_email_html(target_email)

            # add open tracker to html
            tracker = self._add_tracker(TRACKER_EMAIL_OPEN, 'not opened', 0)
            target_email.html_content = self._add_email_traker(target_email,
                                                               tracker)

        # Create landing page tracker
        if landing_page:
            self._add_tracker(TRACKER_LANDING_PAGE_OPEN, 'not opened', 0)

            # add post intecept traker
            if POST_TRACKER_ID in landing_page.html:
                self._add_tracker(TRACKER_LANDING_PAGE_POST, 'no', 0)

        # Create django email object
        mail = EmailMultiAlternatives(
            subject=self._replace_vars(target_email.email_subject),
            body=self._replace_vars(target_email.text_content),
            from_email=target_email.from_email,
            to=[target.email], connection=smtp_connection
        )

        # Add html content in email
        if target_email.html_content:
            mail.attach_alternative(
                self._replace_vars(target_email.html_content),
                'text/html'
            )

        # Add all attachments in email object
        for attachment in attachments:
            mail.attach(**attachment)

        return mail

    def _replace_vars(self, content):
        return replace_template_vars(
            content, self.campaign, self._cache_current_target,
            self.campaign.email_template
        )

    def _make_email_html(self, target_email):
        """Convert email txt to html (if html is empty)"""
        # get content without balise (for empty check)
        content = target_email.html_content
        for r in ('html', 'head', 'title', 'body', '&nbsp;', '<', '/', '>'):
            content = content.replace(r, '')

        # convert txt to html (if html is empty)
        if content.strip():
            return target_email.html_content

        return render_to_string('phishing/email/to_html.html', {
            'lines': target_email.text_content.split('\n')
        })

    def _add_email_traker(self, target_email, tracker):
        """Add email open tracker in html"""
        # get html code of tracking image
        tracking_img = render_to_string(
            'phishing/email/tracker_image.html', {
                'tracker_id': str(tracker.pk),
                'host': HOSTNAME,
            })

        # add tracking image in email
        if '</body>' in target_email.html_content:
            return target_email.html_content.replace(
                '</body>',
                '%s</body>' % tracking_img
            )

        return '%s%s' % (target_email.html_content, tracking_img)

# TODO: sortir la conf smtp => faire un model
#
#  class SmtpServer(Model):
#   host = CharField(_('Custom SMTP hostname'), max_length=128, blank=True)
#   username = CharField(_('Custom SMTP username'),max_length=128, blank=True)
#   password = CharField(_('Custom SMTP password'),max_length=256, blank=True)
#   use_ssl = BooleanField(_('Custom SMTP server use SSL'), blank=True)
#
# TODO: bouton de test de campagne
