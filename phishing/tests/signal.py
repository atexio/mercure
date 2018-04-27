import json
import os

from bs4 import BeautifulSoup
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.db.models.signals import post_save
from django.test import TestCase
from django.urls import reverse
from shutil import copyfile

from phishing.helpers import get_template_vars, replace_template_vars
from phishing.models import Attachment, Campaign, EmailTemplate, LandingPage, \
    Target, TargetGroup, Tracker, TrackerInfos
from phishing.signals import make_campaign_report, make_menu, \
    landing_page_printed, make_template_vars, send_email
from phishing.strings import TRACKER_ATTACHMENT_EXECUTED, TRACKER_EMAIL_OPEN, \
    TRACKER_EMAIL_SEND, TRACKER_LANDING_PAGE_OPEN, TRACKER_LANDING_PAGE_POST


# helpers
from phishing.tests.constant import FILES_PATH


class SearchListMixin(object):
    def _search_name(self, dictionary_list, name):
        """Search by name in list of dictionary"""
        result = [v for v in dictionary_list if v.get('name', '') == name]
        self.assertLessEqual(len(result), 1, 'duplicate: %s' % result)
        return result[0] if len(result) else None


class SuccessException(Exception):
    """Use for unit test check."""
    pass


# test
class EmailTemplateSignalTestCase(TestCase, SearchListMixin):
    # email template
    def get(self, name):
        return self._search_name(get_template_vars(), name)

    def test_add_vars(self):
        # add value handler
        def handler(vars_data, **kwarg):
            vars_data.append({
                'name': 'test_var',
                'description': 'Is a test!',
                'value': 'Hello!',
            })

        make_template_vars.connect(handler)

        # test value
        var_data = self.get('test_var')
        self.assertIsNotNone(var_data)
        self.assertEqual(var_data['value'], 'Hello!')
        self.assertEqual(var_data['description'], 'Is a test!')

        # test replace
        content = replace_template_vars('{{ test_var }}')
        self.assertEqual(content, 'Hello!')

        # clean
        self.assertTrue(make_template_vars.disconnect(handler))

    def test_edit_vars(self):
        # add value handler
        def handler(vars_data, **kwarg):
            var_data = self._search_name(vars_data, 'email')
            self.assertIsNotNone(var_data)
            var_data['value'] = 'Hello Word!'

        make_template_vars.connect(handler)

        # test value
        var_data = self.get('email')
        self.assertIsNotNone(var_data)
        self.assertEqual(var_data['value'], 'Hello Word!')

        # test replace
        content = replace_template_vars('{{ email }}')
        self.assertEqual(content, 'Hello Word!')

        # clean
        self.assertTrue(make_template_vars.disconnect(handler))

    def test_delete_vars(self):
        # add value handler
        def handler(vars_data, **kwarg):
            var_data = self._search_name(vars_data, 'email')
            self.assertIsNotNone(var_data)
            vars_data.remove(var_data)

        make_template_vars.connect(handler)

        # test value
        var_data = self.get('email')
        self.assertIsNone(var_data)

        # test replace
        content = replace_template_vars('{{ email }}')
        self.assertEqual(content, '{{ email }}')

        # clean
        self.assertTrue(make_template_vars.disconnect(handler))


class LandingPageSignalTestCase(TestCase):
    def test_edit_on_call(self):
        # add value handler
        def handler(request, landing_page, **kwarg):
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            landing_page.html = 'Hello world! %s' % user_agent

        landing_page_printed.connect(handler)

        # start campaign and get landing page url
        landing_page = LandingPage.objects.create(
            name='test',
            html='123'
        )
        email_template = EmailTemplate.objects.create(
            name='test',
            email_subject='test',
            from_email='test@test.com',
            landing_page=landing_page,
            text_content='{{ landing_page_url }}',
            html_content=''
        )
        target_group = TargetGroup.objects.create(name='test')
        Target.objects.create(email='test@test.com', group=target_group)
        campaign = Campaign.objects.create(
            name='test',
            email_template=email_template
        )
        campaign.target_groups_add(target_group)
        self.assertTrue(campaign.send())

        landing_page_url = mail.outbox[-1].body.split('<')[0]

        # call landing page ans test result
        self.client.defaults['HTTP_USER_AGENT'] = 'myUserAgent'
        response = self.client.get(landing_page_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode(), 'Hello world! myUserAgent')

        # clean
        self.assertTrue(landing_page_printed.disconnect(handler))


class MenuSignalTestCase(TestCase, SearchListMixin):
    def get(self, name):
        menu = get_user_model()(is_superuser=True).get_menu()  # get full menu
        return self._search_name(menu, name)

    def test_add_item(self):
        # add value handler
        def handler(urls, **kwarg):
            urls.append({
                'name': 'test',
                'url': 'http://google.fr',
            })

        make_menu.connect(handler)

        # test
        item = self.get('test')
        self.assertIsNotNone(item)
        self.assertEqual(item['url'], 'http://google.fr')

        # clean
        self.assertTrue(make_menu.disconnect(handler))

    def test_edit_item(self):
        # add value handler
        def handler(urls, **kwarg):
            item = self._search_name(urls, 'Campaigns')
            self.assertIsNotNone(item)
            item['url'] = 'http://google.fr'

        make_menu.connect(handler)

        # test
        item = self.get('Campaigns')
        self.assertIsNotNone(item)
        self.assertEqual(item['url'], 'http://google.fr')

        # clean
        self.assertTrue(make_menu.disconnect(handler))

    def test_delete_item(self):
        # add value handler
        def handler(urls, **kwarg):
            item = self._search_name(urls, 'Campaigns')
            self.assertIsNotNone(item)
            urls.remove(item)

        make_menu.connect(handler)

        # test
        item = self.get('Campaigns')
        self.assertIsNone(item)

        # clean
        self.assertTrue(make_menu.disconnect(handler))


class CampaignSignalTestCase(TestCase):
    def test_edit_send_email(self):
        # add value handler
        def handler(email_template, **kwarg):
            email_template.text_content = 'Hello!'
            email_template.html_content = 'Hi!'

        send_email.connect(handler)

        # start campaign and get landing page url
        landing_page = LandingPage.objects.create(
            name='test',
            html='123'
        )
        email_template = EmailTemplate.objects.create(
            name='test',
            email_subject='test',
            from_email='test@test.com',
            landing_page=landing_page,
            text_content='{{ landing_page_url }}',
            html_content=''
        )
        target_group = TargetGroup.objects.create(name='test')
        Target.objects.create(email='test@test.com', group=target_group)
        campaign = Campaign.objects.create(
            name='test',
            email_template=email_template
        )
        campaign.target_groups_add(target_group)
        self.assertTrue(campaign.send())

        self.assertEqual(mail.outbox[-1].body, 'Hello!')
        mail_html = mail.outbox[-1].alternatives[0][0]
        self.assertEqual(mail_html.split('<')[0], 'Hi!')

        # clean
        self.assertTrue(send_email.disconnect(handler))


class TargetActionSignalTestCase(TestCase):
    def send_campaign(self):
        # create campaign
        landing_page = LandingPage.objects.create(
            name='test',
            html="""<html>
                <body>
                    <form method="POST">
                        <input name="login" />
                    </form>
                </html>
            """
        )
        # use json build (archive in attachment unit test)
        attachment_path = os.path.join(settings.MEDIA_ROOT, 'test_attachment')
        copyfile(os.path.join(FILES_PATH, 'archive.zip'), attachment_path)
        attachment = Attachment(
            name='test',
            attachment_name='test.doc',
            buildable=True
        )
        attachment.file = os.path.join('..', attachment_path)
        attachment.save()
        email_template = EmailTemplate.objects.create(
            name='test',
            email_subject='test',
            from_email='test@test.com',
            landing_page=landing_page,
            text_content='{{ landing_page_url }}',
            html_content=''
        )
        email_template.attachments.add(attachment)
        target_group = TargetGroup.objects.create(name='test')
        Target.objects.create(email='test@test.com', group=target_group)
        campaign = Campaign.objects.create(
            name='test',
            email_template=email_template
        )
        campaign.target_groups_add(target_group)
        self.assertTrue(campaign.send())

        return campaign

    def test_attachment_executed(self):
        def handler(instance, **kwarg):
            # get post on landing page event
            if instance.target_tracker.key != TRACKER_ATTACHMENT_EXECUTED:
                # ignore other target event
                return

            self.assertEqual(instance.ip, '127.0.0.1')
            self.assertEqual(instance.user_agent, 'Outlook')
            raise SuccessException()

        post_save.connect(handler, sender=TrackerInfos)

        # call tracker
        self.send_campaign()
        attachment = json.loads(mail.outbox[-1].attachments[0][1].decode())
        tracker_url = attachment['tracker_url']

        # test if handler has call
        with self.assertRaises(SuccessException):
            self.client.defaults['HTTP_USER_AGENT'] = 'Outlook'
            self.client.get(tracker_url)

        # clean
        self.assertTrue(post_save.disconnect(handler, sender=TrackerInfos))

    def test_attachment_executed_with_data(self):
        def handler(instance, **kwarg):
            # get post on landing page event
            if instance.target_tracker.key != TRACKER_ATTACHMENT_EXECUTED:
                # ignore other target event
                return

            self.assertEqual(instance.ip, '127.0.0.1')
            self.assertEqual(instance.user_agent, 'Thunderbird')
            self.assertEqual(instance.raw, '{"hello": "world!"}')
            raise SuccessException()

        post_save.connect(handler, sender=TrackerInfos)

        # call tracker
        self.send_campaign()
        attachment = json.loads(mail.outbox[-1].attachments[0][1].decode())
        tracker_url = attachment['tracker_url']

        # test if handler has call
        with self.assertRaises(SuccessException):
            self.client.defaults['HTTP_USER_AGENT'] = 'Thunderbird'
            self.client.post(tracker_url, {'hello': 'world!'})

        # clean
        self.assertTrue(post_save.disconnect(handler, sender=TrackerInfos))

    def test_email_open(self):
        def handler(instance, **kwarg):
            # get email open event
            if instance.target_tracker.key != TRACKER_EMAIL_OPEN:
                # ignore other target event
                return

            self.assertEqual(instance.ip, '127.0.0.1')
            self.assertEqual(instance.user_agent, 'Outlook')
            raise SuccessException()

        post_save.connect(handler, sender=TrackerInfos)

        # call tracker
        self.send_campaign()
        mail_html = mail.outbox[-1].alternatives[0][0]
        tracker_url = mail_html.split('src="')[-1].split('"')[0]

        # test if handler has call
        with self.assertRaises(SuccessException):
            self.client.defaults['HTTP_USER_AGENT'] = 'Outlook'
            self.client.get(tracker_url)

        # clean
        self.assertTrue(post_save.disconnect(handler, sender=TrackerInfos))

    def test_landing_page_open(self):
        def handler(instance, **kwarg):
            # get landing page printed event
            if instance.target_tracker.key != TRACKER_LANDING_PAGE_OPEN:
                # ignore other target event
                return

            self.assertEqual(instance.ip, '127.0.0.1')
            self.assertEqual(instance.user_agent, 'Firefox')
            self.assertEqual(instance.referer, 'https://webmail.com')
            raise SuccessException()

        post_save.connect(handler, sender=TrackerInfos)

        # call tracker
        self.send_campaign()
        tracker_url = mail.outbox[-1].body

        # test if handler has call
        with self.assertRaises(SuccessException):
            self.client.defaults['HTTP_USER_AGENT'] = 'Firefox'
            self.client.defaults['HTTP_REFERER'] = 'https://webmail.com'
            self.client.get(tracker_url)

        # clean
        self.assertTrue(post_save.disconnect(handler, sender=TrackerInfos))

    def test_email_send(self):
        def handler(instance, **kwarg):
            # get email open event
            if instance.key != TRACKER_EMAIL_SEND:
                # ignore other target event
                return

            self.assertEqual(instance.value, 'success')

            # add entry on db for set test in success => SuccessException make
            # infinite loop
            TrackerInfos.objects.create(
                target_tracker=instance,
                raw='handler_%s_test_ok' % TRACKER_EMAIL_SEND
            )

        post_save.connect(handler, sender=Tracker)

        # send mail
        campaign = self.send_campaign()

        # test if handler has call
        raw = 'handler_%s_test_ok' % TRACKER_EMAIL_SEND
        test_result_tracker = TrackerInfos.objects.filter(raw=raw).first()
        self.assertIsNotNone(test_result_tracker)
        tracker = test_result_tracker.target_tracker
        self.assertEqual(campaign.pk, tracker.campaign.pk)
        self.assertEqual(TRACKER_EMAIL_SEND, tracker.key)

        # clean
        self.assertTrue(post_save.disconnect(handler, sender=Tracker))

    def test_landing_page_post(self):
        def handler(instance, **kwarg):
            # get post on landing page event
            if instance.target_tracker.key != TRACKER_LANDING_PAGE_POST:
                # ignore other target event
                return

            self.assertEqual(instance.ip, '127.0.0.1')
            self.assertEqual(instance.user_agent, 'Firefox')
            self.assertEqual(instance.referer, 'https://webmail.com')
            self.assertIn('"login": "Admin"', instance.raw)
            raise SuccessException()

        post_save.connect(handler, sender=TrackerInfos)

        # call tracker
        self.send_campaign()
        tracker_url = mail.outbox[-1].body

        # call landing page
        response = self.client.get(tracker_url)
        self.assertEqual(response.status_code, 200)

        # get form infos
        html = response.content.decode()
        form = BeautifulSoup(html, 'html.parser').find('form')
        post_url = form.get('action')
        post_data = {i.get('name'): i.get('value')
                     for i in form.find_all('input')}
        post_data['login'] = 'Admin'

        # test if handler has call
        with self.assertRaises(SuccessException):
            self.client.defaults['HTTP_USER_AGENT'] = 'Firefox'
            self.client.defaults['HTTP_REFERER'] = 'https://webmail.com'
            self.client.post(post_url, post_data)

        # clean
        self.assertTrue(post_save.disconnect(handler, sender=TrackerInfos))


class ReportSignalTestCase(TestCase):
    def get(self):
        # create campaign
        landing_page = LandingPage.objects.create(
            name='test',
            html='123'
        )
        email_template = EmailTemplate.objects.create(
            name='test',
            email_subject='test',
            from_email='test@test.com',
            landing_page=landing_page,
            text_content='{{ landing_page_url }}',
            html_content=''
        )
        target_group = TargetGroup.objects.create(name='test')
        Target.objects.create(email='test@test.com', group=target_group)
        campaign = Campaign.objects.create(
            name='test',
            email_template=email_template
        )
        campaign.target_groups_add(target_group)
        self.assertTrue(campaign.send())

        # init
        user_infos = {'username': 'default', 'password': 'pass'}
        get_user_model().objects.create_user(**user_infos,
                                             is_superuser=True)
        self.client.login(**user_infos)

        # test
        url = reverse('campaign_dashboard', args=[campaign.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        return response.content.decode()

    def test_add_campaign_report_item(self):
        def handler(context, **kwarg):
            context['tabs_layout']['Test'] = []

        make_campaign_report.connect(handler)

        # test
        content = self.get()
        self.assertIn('<a href="#test" aria-controls="test" role="tab" '
                      'data-toggle="tab">Test</a>', content)
        self.assertIn('id="test"', content)

        # clean
        self.assertTrue(make_campaign_report.disconnect(handler))

    def test_edit_campaign_report_item(self):
        def handler(context, **kwarg):
            context['tabs_layout']['Test'] = context['tabs_layout']. \
                pop('Other')

        make_campaign_report.connect(handler)

        # test
        content = self.get()
        self.assertIn('<a href="#test" aria-controls="test" role="tab" '
                      'data-toggle="tab">Test</a>', content)
        self.assertIn('id="test"', content)
        self.assertNotIn('<a href="#other" aria-controls="other" '
                         'role="tab" data-toggle="tab">Other</a>', content)
        self.assertNotIn('id="other"', content)

        # clean
        self.assertTrue(make_campaign_report.disconnect(handler))

    def test_delete_campaign_report_item(self):
        def handler(context, **kwarg):
            del(context['tabs_layout']['Other'])

        make_campaign_report.connect(handler)

        # test
        content = self.get()
        self.assertNotIn('<a href="#other" aria-controls="other" '
                         'role="tab" data-toggle="tab">Other</a>', content)
        self.assertNotIn('id="other"', content)

        # clean
        self.assertTrue(make_campaign_report.disconnect(handler))
