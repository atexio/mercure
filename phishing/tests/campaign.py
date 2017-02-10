import json
import os

from django.core import mail
from django.test import TestCase
from django.urls import reverse

from phishing.models import Campaign
from phishing.models import EmailTemplate
from phishing.models import LandingPage
from phishing.models import Target
from phishing.models import TargetGroup
from phishing.models import TrackerInfos
from phishing.strings import TRACKER_EMAIL_OPEN, TRACKER_LANDING_PAGE_OPEN, \
    TRACKER_LANDING_PAGE_POST
from phishing.tests.constant import FIXTURE_PATH


class CampaignTestCase(TestCase):
    fixtures = [
        os.path.join(FIXTURE_PATH, 'user.json'),
    ]

    def test_context_data_campaign(self):
        self.client.login(username='admin', password='supertest')
        resp = self.client.get(reverse('campaign_add'))
        self.assertEqual(resp.context['form'].fields['smtp_use_ssl'].label,
                         'Use SSL')

    def test_dashboard_campaign_target_groups(self):
        # add landing page
        landing_page = LandingPage.objects.create(
            domain='https://my-fake-domain.com',
            html='<form><input name="test"></form>',
            name='name',
        )

        # add email template
        email_template = EmailTemplate.objects.create(
            email_subject='Hello!',
            from_email='account@example.com',
            landing_page=landing_page,
            name='email template name',
            text_content='Goodbye!',
        )

        # create campaign
        campaign = Campaign.objects.create(
            email_template=email_template,
            name='test group graph',
        )

        # add targets emails
        target_group1_emails = ('a@test.com', 'b@test.com')
        target_group1_name = 'target group 1 name'
        target_group1 = TargetGroup.objects.create(name=target_group1_name)

        for email in target_group1_emails:
            Target.objects.create(email=email, group=target_group1)
        campaign.target_groups.add(target_group1)

        target_group2_emails = ('b@test.com', 'c@test.com')
        target_group2_name = 'target group 2 name'
        target_group2 = TargetGroup.objects.create(name=target_group2_name)

        for email in target_group2_emails:
            Target.objects.create(email=email, group=target_group2)
        campaign.target_groups.add(target_group2)

        # find and increase tracker
        def add_tracker_entry(tracker_key, email):
            for tracker in campaign.trackers.filter(key=tracker_key).all():
                if email == tracker.target.email:
                    # add counter
                    if not tracker.infos:
                        tracker.infos = 1
                    else:
                        tracker.infos += 1

                    tracker.save()
                    return tracker

            self.fail('tracker not found (%s: %s)' % (tracker_key, email))

        add_tracker_entry(TRACKER_EMAIL_OPEN, 'a@test.com')
        add_tracker_entry(TRACKER_EMAIL_OPEN, 'b@test.com')

        add_tracker_entry(TRACKER_LANDING_PAGE_OPEN, 'b@test.com')
        add_tracker_entry(TRACKER_LANDING_PAGE_OPEN, 'c@test.com')

        add_tracker_entry(TRACKER_LANDING_PAGE_POST, 'a@test.com')
        add_tracker_entry(TRACKER_LANDING_PAGE_POST, 'b@test.com')
        add_tracker_entry(TRACKER_LANDING_PAGE_POST, 'c@test.com')

        # check values
        campaign.target_groups.add(target_group1)
        url = reverse('campaign_dashboard', args=(campaign.pk,))
        self.client.login(username='admin', password='supertest')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

        def check(var_name, group1_count, group2_count):
            test_infos = '(var_name: %s, group1_count: %s, group2_count : %s)'\
                         % (var_name, group1_count, group2_count)

            search = [l for l in resp.content.decode().split('\n')
                      if '%s:' % var_name in l]
            if not search:
                self.fail('js line not found' + test_infos)

            line = search[0]
            data = json.loads(
                line.split(':', 1)[1].rsplit(',', 1)[0]  # get js data
                    .replace("'", '"')  # convert to json
            )

            # check values
            self.assertEqual(data.get(target_group1_name, 0), group1_count,
                             test_infos)
            self.assertEqual(data.get(target_group2_name, 0), group2_count,
                             test_infos)

        # email open check
        self.assertContains(resp, 'id="target_group_email_open_pie"')
        check('target_group_email_open_pie', 2, 1)

        # open landing page
        self.assertContains(resp, 'id="target_group_landing_page_open_pie"')
        check('target_group_landing_page_open_pie', 1, 2)

        # post landing page
        self.assertContains(resp, 'id="target_group_landing_page_post_pie"')
        check('target_group_landing_page_post_pie', 2, 2)

    def test_dashboard_campaign_without_landing_page(self):
        self.client.login(username='admin', password='supertest')

        # add targets emails
        target_group1_emails = ('a@test.com', 'b@test.com', 'c@test.com')
        target_group1_title = 'target group 1 title'
        target_group1 = TargetGroup.objects.create(name=target_group1_title)

        for email in target_group1_emails:
            Target.objects.create(email=email, group=target_group1)

        # add email template
        email_template_content = 'click: {{ landing_page_url }}'
        email_template_from = 'account@example.com'
        email_template_name = 'email template title'
        email_template_subject = 'Hello!'
        email_template = EmailTemplate.objects.create(
            email_subject=email_template_subject,
            from_email=email_template_from,
            landing_page=None,
            name=email_template_name,
            text_content=email_template_content,
        )

        # create campaign
        campaign_name = 'campaign title'
        campaign = Campaign.objects.create(
            email_template=email_template,
            name=campaign_name,
        )

        # send emails to group 1
        campaign.target_groups.add(target_group1)

        for track in campaign.trackers.all():
            TrackerInfos.create(target_tracker=track)

        # send emails to group 1
        campaign.target_groups.add(target_group1)
        resp = self.client.get(reverse('campaign_dashboard',
                                       args=(campaign.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="all_histogram"')
        self.assertContains(resp, 'id="email_send_pie"')
        self.assertContains(resp, 'id="all_histogram"')
        self.assertContains(resp, 'id="email_send_pie"')
        self.assertNotContains(resp, 'id="landing_page_open_pie"')
        self.assertNotContains(resp, 'id="post_on_landing_page_pie"')

    def test_dashboard_campaign_with_landing_page(self):
        self.client.login(username='admin', password='supertest')

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
        # add targets emails
        target_group1_emails = ('a@test.com', 'b@test.com', 'c@test.com')
        target_group1_title = 'target group 1 title'
        target_group1 = TargetGroup.objects.create(name=target_group1_title)

        for email in target_group1_emails:
            Target.objects.create(email=email, group=target_group1)

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

        # create campaign
        campaign_name = 'campaign title'
        campaign = Campaign.objects.create(
            email_template=email_template,
            name=campaign_name,
        )

        # send emails to group 1
        campaign.target_groups.add(target_group1)

        for track in campaign.trackers.all():
            TrackerInfos.create(target_tracker=track)

        # send emails to group 1
        campaign.target_groups.add(target_group1)
        resp = self.client.get(reverse('campaign_dashboard',
                                       args=(campaign.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="all_histogram"')
        self.assertContains(resp, 'id="email_send_pie"')
        self.assertContains(resp, 'id="all_histogram"')
        self.assertContains(resp, 'id="email_send_pie"')
        self.assertContains(resp, 'id="landing_page_open_pie"')
        self.assertNotContains(resp, 'id="post_on_landing_page_pie"')

    def test_dashboard_campaign_with_smtp(self):
        self.client.login(username='admin', password='supertest')

        # add targets emails
        target_group1_emails = ('a@test.com', 'b@test.com', 'c@test.com')
        target_group1_title = 'target group 1 title'
        target_group1 = TargetGroup.objects.create(name=target_group1_title)

        for email in target_group1_emails:
            Target.objects.create(email=email, group=target_group1)

        # add email template
        email_template_content = 'click: {{ landing_page_url }}'
        email_template_from = 'account@example.com'
        email_template_name = 'email template title'
        email_template_subject = 'Hello!'
        email_template = EmailTemplate.objects.create(
            email_subject=email_template_subject,
            from_email=email_template_from,
            landing_page=None,
            name=email_template_name,
            text_content=email_template_content,
        )

        # create campaign
        campaign_name = 'campaign title'
        campaign = Campaign.objects.create(
            email_template=email_template,
            name=campaign_name,
            smtp_use_ssl=True,
            smtp_host="127.0.0.1:8000",
            smtp_username="admin",
            smtp_password="supertest",
        )

        # send emails to group 1
        campaign.target_groups.add(target_group1)

        for track in campaign.trackers.all():
            TrackerInfos.create(target_tracker=track)

        # send emails to group 1, need to test it with valid credential
        campaign.target_groups.add(target_group1)
        resp = self.client.get(reverse('campaign_dashboard',
                                       args=(campaign.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="all_histogram"')
        self.assertContains(resp, 'id="email_send_pie"')
        self.assertContains(resp, 'id="all_histogram"')
        self.assertContains(resp, 'id="email_send_pie"')
        self.assertNotContains(resp, 'id="landing_page_open_pie"')
        self.assertNotContains(resp, 'id="post_on_landing_page_pie"')

    def test_dashboard_campaign_with_minimize_url(self):
        self.client.login(username='admin', password='supertest')

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
        # add targets emails
        target_group1_emails = ('a@test.com', 'b@test.com', 'c@test.com')
        target_group1_title = 'target group 1 title'
        target_group1 = TargetGroup.objects.create(name=target_group1_title)

        for email in target_group1_emails:
            Target.objects.create(email=email, group=target_group1)

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

        # create campaign
        campaign_name = 'campaign title'
        campaign = Campaign.objects.create(
            email_template=email_template,
            name=campaign_name,
            minimize_url=True,
        )

        # send emails to group 1
        campaign.target_groups.add(target_group1)

        # check minified url
        self.assertIn('click: http://tinyurl.com/',
                      str(mail.outbox[-1].message()))

        for track in campaign.trackers.all():
            TrackerInfos.create(target_tracker=track)

        # send emails to group 1
        campaign.target_groups.add(target_group1)
        resp = self.client.get(reverse('campaign_dashboard',
                                       args=(campaign.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="all_histogram"')
        self.assertContains(resp, 'id="email_send_pie"')
        self.assertContains(resp, 'id="all_histogram"')
        self.assertContains(resp, 'id="email_send_pie"')
        self.assertContains(resp, 'id="landing_page_open_pie"')
        self.assertNotContains(resp, 'id="post_on_landing_page_pie"')

    def test_dashboard_campaign_with_incorrect_htmlcontent_email(self):
        self.client.login(username='admin', password='supertest')

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
        # add targets emails
        target_group1_emails = ('a@test.com', 'b@test.com', 'c@test.com')
        target_group1_title = 'target group 1 title'
        target_group1 = TargetGroup.objects.create(name=target_group1_title)

        for email in target_group1_emails:
            Target.objects.create(email=email, group=target_group1)

        # add email template
        email_template_content = 'click: {{ landing_page_url }}'
        email_html_content = '<!DOCTYPE html>' \
                             '<html lang="en">' \
                             '</html>'
        email_template_from = 'account@example.com'
        email_template_name = 'email template title'
        email_template_subject = 'Hello!'
        email_template = EmailTemplate.objects.create(
            email_subject=email_template_subject,
            from_email=email_template_from,
            landing_page=landing_page,
            name=email_template_name,
            text_content=email_template_content,
            html_content=email_html_content,
        )

        # create campaign
        campaign_name = 'campaign title'
        campaign = Campaign.objects.create(
            email_template=email_template,
            name=campaign_name,
            minimize_url=True,
        )

        # send emails to group 1
        campaign.target_groups.add(target_group1)

        for track in campaign.trackers.all():
            TrackerInfos.create(target_tracker=track)

        # send emails to group 1
        campaign.target_groups.add(target_group1)
        resp = self.client.get(reverse('campaign_dashboard',
                                       args=(campaign.pk,)))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'id="all_histogram"')
        self.assertContains(resp, 'id="email_send_pie"')
        self.assertContains(resp, 'id="all_histogram"')
        self.assertContains(resp, 'id="email_send_pie"')
        self.assertContains(resp, 'id="landing_page_open_pie"')
        self.assertNotContains(resp, 'id="post_on_landing_page_pie"')

    # TODO:Check if someone post on landing page
    # def _test_dashboard_campaign_with_landing_page_and_response(self):
    #     self.client.login(username='admin', password='supertest')
    #
    #     # add landing page
    #     landing_page_domain = 'https://my-fake-domain.com'
    #     landing_page_html = '<!DOCTYPE html>' \
    #                         '<html lang="en">' \
    #                         '<body>' \
    #                         'test' \
    #                         '</body>' \
    #                         '</html>'
    #     landing_page_name = 'landing page title'
    #     landing_page = LandingPage.objects.create(
    #         domain=landing_page_domain,
    #         html=landing_page_html,
    #         name=landing_page_name,
    #     )
    #     # add targets emails
    #     target_group1_emails = ('a@test.com', 'b@test.com', 'c@test.com')
    #     target_group1_title = 'target group 1 title'
    #     target_group1 = TargetGroup.objects.create(name=target_group1_title)
    #
    #     for email in target_group1_emails:
    #         Target.objects.create(email=email, group=target_group1)
    #
    #     # add email template
    #     email_template_content = 'click: {{ landing_page_url }}'
    #     email_template_from = 'account@example.com'
    #     email_template_name = 'email template title'
    #     email_template_subject = 'Hello!'
    #     email_template = EmailTemplate.objects.create(
    #         email_subject=email_template_subject,
    #         from_email=email_template_from,
    #         landing_page=landing_page,
    #         name=email_template_name,
    #         text_content=email_template_content,
    #     )
    #
    #     # create campaign
    #     campaign_name = 'campaign title'
    #     campaign = Campaign.objects.create(
    #         email_template=email_template,
    #         name=campaign_name,
    #     )
    #
    #     # send emails to group 1
    #     campaign.target_groups.add(target_group1)
    #
    #     for track in campaign.trackers.all():
    #         tracker_infos = TrackerInfos.create(target_tracker=track)
    #
    #     # send emails to group 1
    #     campaign.target_groups.add(target_group1)
    #     resp = self.client.get(reverse('campaign_dashboard',
    #                                    args=(campaign.pk,)))
    #     self.assertEqual(resp.status_code, 200)
    #     self.assertContains(resp, 'id="all_histogram"')
    #     self.assertContains(resp, 'id="email_send_pie"')
    #     self.assertContains(resp, 'id="all_histogram"')
    #     self.assertContains(resp, 'id="email_send_pie"')
    #     self.assertContains(resp, 'id="landing_page_open_pie"')
    #     self.assertContains(resp, 'id="post_on_landing_page_pie"')
