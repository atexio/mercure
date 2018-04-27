import os

from django.core import mail
from django.test import TestCase
from shutil import copyfile


from phishing.models import Attachment, Campaign, EmailTemplate, LandingPage,\
    Target, TargetGroup


class ScenarioTestCase(TestCase):
    def test_scenario(self):
        # add landing page
        landing_page_domain = 'https://my-fake-domain.com'
        landing_page_html = '<!DOCTYPE html>' \
                            '<html lang="en">' \
                            '<body>' \
                            'test' \
                            '</body>' \
                            '</html>'
        landing_page_name = 'landing page title'
        landing_page = LandingPage.objects.create(
            domain=landing_page_domain,
            html=landing_page_html,
            name=landing_page_name,
        )

        # add email template
        email_template_content = 'click: {{ landing_page_url }}'
        email_template_from = 'account@example.com'
        email_template_name = 'email template title'
        email_template_subject = 'Hello!'
        email_template = EmailTemplate.objects.create(
            email_subject=email_template_subject,
            from_email=email_template_from,
            landing_page=landing_page,
            name=email_template_name,
            text_content=email_template_content,
        )

        self.assertEqual(landing_page, email_template.landing_page)

        # add attachment
        files_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'files')

        attachment_1_name = 'b64.png'
        attachment_1_path = 'media/test_attachment_1'
        copyfile(os.path.join(files_path, 'image.png'), attachment_1_path)
        attachment_1 = Attachment(
            name=attachment_1_name,
            buildable=False
        )
        attachment_1.file = os.path.join('..', attachment_1_path)
        attachment_1.save()
        email_template.attachments.add(attachment_1)

        attachment_2_name = 'build.json'
        attachment_2_path = 'media/test_attachment_2'
        copyfile(os.path.join(files_path, 'archive.zip'), attachment_2_path)
        attachment_2 = Attachment(
            name=attachment_2_name,
            buildable=True
        )
        attachment_2.file = os.path.join('..', attachment_2_path)
        attachment_2.save()
        email_template.attachments.add(attachment_2)

        # add targets emails
        target_group1_emails = ('a@test.com', 'b@test.com', 'c@test.com')
        target_group1_title = 'target group 1 title'
        target_group1 = TargetGroup.objects.create(name=target_group1_title)

        for email in target_group1_emails:
            Target.objects.create(email=email, group=target_group1)

        self.assertEqual(len(target_group1.targets.all()), 3)

        # add other target group
        target_group2_emails = ('z@test.com', 'b@test.com')
        target_group2_title = 'target group 2 title'
        target_group2 = TargetGroup.objects.create(name=target_group2_title)

        for email in target_group2_emails:
            Target.objects.create(email=email, group=target_group2)

        self.assertEqual(len(target_group2.targets.all()), 2)

        # create campaign
        campaign_name = 'campaign title'
        campaign = Campaign.objects.create(
            email_template=email_template,
            name=campaign_name,
        )

        self.assertEqual(len(mail.outbox), 0)  # not email sended

        # send emails to group 1
        campaign.target_groups_add(target_group1)
        self.assertTrue(campaign.send())

        # There is three target and four trackers by target,
        # so we must have 12 trackers at all
        trackers_count = campaign.trackers.count()

        # If you need some debug on why your email is in fail state ;)
        # if campaign.trackers.filter(key='email_send', value='fail').exists():
        #     # debug for email send error
        #     print('error details:')
        #     for name, value in campaign.trackers.first().__dict__.items():
        #         if not name.startswith('_'):
        #             print(' %s: %s' % (name, value))

        self.assertEqual(trackers_count, 12, campaign.trackers.all())
        self.assertEqual(len(mail.outbox), 3, mail.outbox)
        self.assertIn('click: %s' % landing_page_domain, mail.outbox[0].body)

        for email in mail.outbox:
            message = email.message()
            self.assertEqual(message['Subject'], email_template_subject)
            self.assertEqual(message['From'], email_template_from)
            self.assertIn(message['To'], target_group1_emails)

        # We send campaign to target_group2.
        # So we must have the previous 10 trackers and 4 more, so 16 at all
        campaign.target_groups_add(target_group2)
        self.assertTrue(campaign.send())

        self.assertEqual(campaign.trackers.count(), 16)
        self.assertEqual(len(mail.outbox), 4)
        message = mail.outbox[-1].message()
        self.assertEqual(message['Subject'], email_template_subject)
        self.assertEqual(message['From'], email_template_from)
        self.assertEqual(message['To'], 'z@test.com')

        # clean
        os.remove(attachment_1_path)
        os.remove(attachment_2_path)
