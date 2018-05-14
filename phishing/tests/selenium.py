import os
from time import sleep

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.urls import reverse
from django.test import tag


from selenium import webdriver
from selenium.webdriver.support.ui import Select

from phishing.models import Campaign, TargetGroup, LandingPage, EmailTemplate
from phishing.tests.constant import FIXTURE_PATH


@tag('selenium')
class SeleniumTestCase(StaticLiveServerTestCase):
    fixtures = [
        os.path.join(FIXTURE_PATH, 'landing_page.json'),
        os.path.join(FIXTURE_PATH, 'target.json'),
        os.path.join(FIXTURE_PATH, 'template.json'),
        os.path.join(FIXTURE_PATH, 'user.json'),
    ]

    def setUp(self):
        # We use a remote Chrome
        username = os.environ.get('SAUCE_USERNAME')
        accesskey = os.environ.get('SAUCE_ACCESS_KEY')
        desired_cap = {
            'platform': "Mac OS X 10.9",
            'browserName': "chrome",
            'version': "31",
            'tunnel-identifier': os.environ.get('TRAVIS_JOB_NUMBER')
        }
        self.drv = webdriver.Remote(
            command_executor='http://%s:%s@ondemand.saucelabs.com/wd/hub'
                             % (username, accesskey),
            desired_capabilities=desired_cap,
        )
        super(SeleniumTestCase, self).setUp()

    def tearDown(self):
        self.drv.quit()
        super(SeleniumTestCase, self).tearDown()

    def abs_url(self, relative_url):
        return self.live_server_url + relative_url

    def login(self, user, passwd):
        self.drv.get(self.abs_url(reverse('login')))
        self.drv.find_element_by_id('id_username').send_keys(user)
        self.drv.find_element_by_id('id_password').send_keys(passwd)
        self.drv.find_element_by_id('id_password').submit()

    def addCampaign(self, name, template, target):
        self.drv.get(self.abs_url(reverse('campaign_add')))

        self.drv.find_element_by_id('id_name').send_keys(name)
        self.fast_multiselect('id_email_template', template)
        self.fast_multiselect('id_target_groups', target)
        self.drv.find_element_by_id('id_name').submit()
        Campaign.send_all()

    def fast_multiselect(self, element_id, labels):
        select = Select(self.drv.find_element_by_id(element_id))
        for label in labels:
            select.select_by_visible_text(label)

    def test_login(self):
        self.drv.get(self.abs_url(reverse('campaign_list')))
        self.assertIn('login/?next=', self.drv.current_url)

        self.login('admin', 'admin')
        body = self.drv.find_element_by_tag_name('body').text
        self.assertIn('Your username and password didn\'t match', body)

        self.login('admin', 'supertest')
        self.assertEquals(self.abs_url(reverse('campaign_list')),
                          self.drv.current_url)

    def test_addCampaign(self):
        self.login('admin', 'supertest')

        # We check that the "Start new campaign" button is working
        self.drv.get(self.abs_url(reverse('campaign_list')))
        self.drv.find_element_by_id('addCampaign').click()
        self.assertEqual(self.abs_url(reverse('campaign_add')),
                         self.drv.current_url)

        self.addCampaign('Test campaign',
                         template=['Test template'],
                         target=['Test'])

        # We check that we are redirected to campaign_list
        self.assertEqual(self.abs_url(reverse('campaign_list')),
                         self.drv.current_url)

        campaign = Campaign.objects.filter(name='Test campaign')
        self.assertEqual(campaign.count(), 1)

        # We click on the new campaign to get dashboard
        # self.selenium.find_element_by_id('campaign_1').click()
        # self.assertEqual(self.abs_url(reverse('campaign_dashboard',
        #                                       args=(1,))),
        #                 self.selenium.current_url)

    def test_dashboard(self):
        self.login('admin', 'supertest')

        # We test with a simple campaign without landing page
        self.addCampaign('Test dashboard',
                         template=['Test template'],
                         target=['Test'])

        camp = Campaign.objects.filter(name='Test dashboard').first()
        self.drv.get(
            self.abs_url(reverse('campaign_dashboard', args=(camp.pk,)))
        )
        body = self.drv.find_element_by_tag_name('body').text
        self.assertIn('Emails open', body)
        self.assertNotIn('Landing page open', body)

        # We add a new campaign with landing page
        self.addCampaign('Test dashboard 2',
                         template=['Test template with landing'],
                         target=['Test'])

        camp = Campaign.objects.filter(name='Test dashboard 2').first()
        self.drv.get(
            self.abs_url(reverse('campaign_dashboard', args=(camp.pk,)))
        )
        body = self.drv.find_element_by_tag_name('body').text
        self.assertIn('Emails open', body)
        self.assertIn('Landing page open', body)

        # TODO: Test landing page post

    def test_click_ajax(self):
        self.login('admin', 'supertest')

        # Test target group
        self.drv.get(self.abs_url(reverse('target_group_list')))
        self.drv.find_element_by_id('targetgroup_1').click()
        self.assertEqual(self.abs_url(reverse('target_group_edit', args=(1,))),
                         self.drv.current_url)

        # Test landing page
        self.drv.get(self.abs_url(reverse('landing_page_list')))
        self.drv.find_element_by_id('landingpage_1').click()
        self.assertEqual(self.abs_url(reverse('landing_page_edit', args=(1,))),
                         self.drv.current_url)

        # Test email template
        self.drv.get(self.abs_url(reverse('email_template_list')))
        self.drv.find_element_by_id('emailtemplate_1').click()
        self.assertEqual(self.abs_url(reverse('email_template_edit',
                                              args=(1,))),
                         self.drv.current_url)

        # Test campaign
        self.addCampaign('Test click ajax',
                         template=['Test template'],
                         target=['Test'])

        cpk = Campaign.objects.filter(name='Test click ajax').first().pk
        self.drv.get(self.abs_url(reverse('campaign_list')))
        self.drv.find_element_by_id('campaign_%s' % cpk).click()
        self.assertEqual(self.abs_url(reverse('campaign_dashboard',
                                              args=(cpk,))),
                         self.drv.current_url)

    def test_delete_ajax(self):
        self.login('admin', 'supertest')

        # Test target group
        targetgrp = TargetGroup.objects.create(
            name='Test delete ajax'
        )

        self.drv.get(self.abs_url(reverse('target_group_list')))
        self.drv.find_element_by_id('delete_targetgroup_%s' % targetgrp.pk)\
            .click()
        self.drv.switch_to.alert.accept()
        # Seem mandatory to handle the javascript redirect after delete
        sleep(1)
        self.assertEqual(self.abs_url(reverse('target_group_list')),
                         self.drv.current_url)

        # Test landing page
        landing = LandingPage.objects.create(
            name='Test delete ajax',
            html='<html></html>'
        )
        self.drv.get(self.abs_url(reverse('landing_page_list')))
        self.drv.find_element_by_id('delete_landingpage_%s' % landing.pk)\
            .click()
        self.drv.switch_to.alert.accept()
        # Seem mandatory to handle the javascript redirect after delete
        sleep(1)
        self.assertEqual(self.abs_url(reverse('landing_page_list')),
                         self.drv.current_url)

        # Test email template
        tpl = EmailTemplate.objects.create(
            name='Test delete ajax',
            email_subject='Test delete ajax',
            from_email='jdoe@atexio.fr',
            text_content='hello'
        )
        self.drv.get(self.abs_url(reverse('email_template_list')))
        self.drv.find_element_by_id('delete_emailtemplate_%s' % tpl.pk).click()
        self.drv.switch_to.alert.accept()
        # Seem mandatory to handle the javascript redirect after delete
        sleep(1)
        self.assertEqual(self.abs_url(reverse('email_template_list')),
                         self.drv.current_url)

        # Test campaign
        self.addCampaign('Test delete ajax',
                         template=['Test template'],
                         target=['Test'])
        camp = Campaign.objects.filter(name='Test delete ajax').first()
        self.drv.get(self.abs_url(reverse('campaign_list')))
        self.drv.find_element_by_id('delete_campaign_%s' % camp.pk).click()
        self.drv.switch_to.alert.accept()
        # Seem mandatory to handle the javascript redirect after delete
        sleep(1)
        self.assertEqual(self.abs_url(reverse('campaign_list')),
                         self.drv.current_url)

    def test_template_clone(self):
        self.login('admin', 'supertest')

        tpl = EmailTemplate.objects.create(
            name='Test clone',
            email_subject='Test clone',
            from_email='jdoe@atexio.fr',
            text_content='hello'
        )

        # At this point we need to have 3 email templates
        # 2 from fixtures, and the new one
        self.assertEqual(EmailTemplate.objects.count(), 3)

        self.drv.get(self.abs_url(reverse('email_template_list')))
        self.drv.find_element_by_id(
            'clone_emailtemplate_%s' % tpl.pk).click()

        # At this point we need to have 4 email templates
        # 2 from fixtures, the original and the clone
        self.assertEqual(EmailTemplate.objects.count(), 4)

        # We retrieve the new email template
        newtpl = EmailTemplate.objects.get(pk=tpl.pk+1)

        # Test newtpl attributes
        self.assertEqual(newtpl.name, '[Clone] Test clone')
        self.assertEqual(tpl.email_subject, newtpl.email_subject)
        self.assertEqual(tpl.from_email, newtpl.from_email)
        self.assertEqual(tpl.has_open_tracker, newtpl.has_open_tracker)
        self.assertEqual(tpl.text_content, newtpl.text_content)
        self.assertEqual(tpl.html_content, newtpl.html_content)
        self.assertEqual(tpl.landing_page, newtpl.landing_page)
