import bs4 as BeautifulSoup
import os
import requests

from django.test import TestCase
from django.urls import reverse

from phishing.helpers import clone_url, intercept_html_post
from phishing.models import LandingPage, Campaign, TargetGroup, Tracker, \
    EmailTemplate, TrackerInfos
from phishing.strings import POST_DOMAIN, TRACKER_LANDING_PAGE_POST, \
    POST_TRACKER_ID
from phishing.tests.constant import FILES_PATH, FIXTURE_PATH


class LandingPageTestCase(TestCase):
    fixtures = [
        os.path.join(FIXTURE_PATH, 'target.json'),
        os.path.join(FIXTURE_PATH, 'user.json'),
    ]

    def test_add_landing_page(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        data = {
            'name': 'Test add landing page',
            'domain': 'http://test.com',
            'html': '<html></html>',
        }
        resp = self.client.post(reverse('landing_page_add'), data=data)
        self.assertRedirects(resp, reverse('landing_page_list'))

        qs = LandingPage.objects.filter(name='Test add landing page')
        self.assertEqual(qs.count(), 1)

        lp = qs.first()
        self.assertEqual(lp.domain, 'http://test.com')
        self.assertEqual(lp.html, '<html><head></head><body></body></html>')

    def test_add_landing_page_invalid_domain(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        data = {
            'name': 'Test add landing page',
            'domain': 'invalid domain',
            'html': '<html></html>',
        }

        # Test invalid domain'
        resp = self.client.post(reverse('landing_page_add'), data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Enter a valid URL.')

    def test_add_landing_page_domain_no_scheme(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        data = {
            'name': 'Test add landing page duplicate',
            'domain': 'test.com',
            'html': '<html></html>',
        }

        resp = self.client.post(reverse('landing_page_add'), data=data)
        self.assertRedirects(resp, reverse('landing_page_list'))

        lp = LandingPage.objects.filter(name=data['name']).first()
        self.assertEqual(lp.domain, 'http://test.com')

    def test_add_landing_page_duplicate(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        data = {
            'name': 'Test add landing page duplicate',
            'domain': 'test.com',
            'html': '<html></html>',
        }

        # We first add a correct landing page
        resp = self.client.post(reverse('landing_page_add'), data=data)
        self.assertRedirects(resp, reverse('landing_page_list'))

        # We try to add a new landing page with the same values
        resp = self.client.post(reverse('landing_page_add'), data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Landing page with this Landing '
                                  'page name already exists.')

    def test_add_landing_page_permissions(self):
        resp = self.client.get(reverse('landing_page_add'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp['Location'],
                      '%s?next=%s' % (reverse('login'),
                                      reverse('landing_page_add')))

        # We log as admin
        self.client.login(username='admin', password='supertest')
        resp = self.client.get(reverse('landing_page_add'))
        self.assertEqual(resp.status_code, 200)

        # TODO: Test user that is not admin

    def test_edit_landing_page(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We create a landing page
        lp = LandingPage.objects.create(
            name='Test edit',
            html='<html></html>'
        )

        data = {
            'name': 'test name',
            'html': 'test html',
            'domain': 'test.com'
        }
        resp = self.client.post(reverse('landing_page_edit', args=(lp.pk,)),
                                data=data)
        self.assertRedirects(resp, reverse('landing_page_list'))

        # We check that the object is updated in database
        lp_test = LandingPage.objects.get(pk=lp.pk)
        self.assertEqual(lp_test.name, 'test name')
        self.assertEqual(lp_test.html,
                         '<html><head></head><body>test html</body></html>')
        self.assertEqual(lp_test.domain, 'http://test.com')
        self.assertEqual(lp_test.pk, lp.pk)

    def test_edit_landing_page_permissions(self):
        # We create a landing page
        lp = LandingPage.objects.create(
            name='Test edit perm',
            html='<html></html>'
        )

        url = reverse('landing_page_edit', args=(lp.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp['Location'], '%s?next=%s' % (reverse('login'), url))

        # We log as admin
        self.client.login(username='admin', password='supertest')
        resp = self.client.get(reverse('landing_page_edit', args=(lp.pk,)))
        self.assertEqual(resp.status_code, 200)

        # TODO: Test user that is not admin

    def test_delete_landing_page(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We create a landing page
        lp = LandingPage.objects.create(
            name='Test delete',
            html='<html></html>'
        )

        # We remove it and check that it correctly redirect
        resp = self.client.post(reverse('landing_page_delete', args=(lp.pk,)))
        self.assertRedirects(resp, reverse('landing_page_list'))

        # We check that the landing page doesn't exists anymor
        self.assertEqual(LandingPage.objects.filter(pk=lp.pk).count(), 0)

    def test_delete_landing_page_permissions(self):
        # We create a landing page
        lp = LandingPage.objects.create(
            name='Test delete perm',
            html='<html></html>'
        )

        url = reverse('landing_page_delete', args=(lp.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp['Location'], '%s?next=%s' % (reverse('login'), url))

        # We log as admin
        self.client.login(username='admin', password='supertest')
        resp = self.client.get(reverse('landing_page_delete', args=(lp.pk,)))
        self.assertEqual(resp.status_code, 200)

        # TODO: Test user that is not admin

    def test_clone_url_permissions(self):
        target = 'http://perdu.com'

        # We test that unauthenticated can't access this page
        resp = self.client.post(reverse('landing_page_clone_url'),
                                data={'url': target})
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp['Location'],
                      '%s?next=%s' % (reverse('login'),
                                      reverse('landing_page_clone_url')))

        # TODO: Test user that is not admin

    def test_clone_url_regular(self):
        target = 'http://perdu.com'

        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We first clone a simple site and compare body that must be identical
        resp = requests.get(target)
        cloneresp = self.client.post(reverse('landing_page_clone_url'),
                                     data={'url': target})

        html = bytes(resp.text, resp.encoding).decode('utf8')  # to utf8
        soup = BeautifulSoup.BeautifulSoup(html, 'html5lib')

        clonesoup = BeautifulSoup.BeautifulSoup(cloneresp.content.decode(),
                                                'html5lib')

        # Check that the bodies are the same
        self.assertEqual(soup.find('body'), clonesoup.find('body'))

        # Check that a base tag has been added
        self.assertEqual(clonesoup.find('base').get('href'), target)

    def test_clone_url_invalid_args(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We test the view without valid arguments
        resp = self.client.post(reverse('landing_page_clone_url'),
                                data={'foo': 'bar'})
        self.assertEqual(resp.status_code, 400)

    def test_clone_url_without_scheme(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We test an URL without scheme
        cloneresp = self.client.post(reverse('landing_page_clone_url'),
                                     data={'url': 'perdu.com'})
        self.assertEqual(cloneresp.status_code, 200)

        # We campare with the original one
        resp = requests.get('http://perdu.com')

        html = bytes(resp.text, resp.encoding).decode('utf8')  # to utf8
        soup = BeautifulSoup.BeautifulSoup(html, 'html5lib')

        clonesoup = BeautifulSoup.BeautifulSoup(cloneresp.content.decode(),
                                                'html5lib')

        self.assertEqual(soup.find('body'), clonesoup.find('body'))

    def test_clone_url_with_form(self):
        target = 'http://www.simplehtmlguide.com/examples/forms1.html'

        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We test an URL with a form
        resp = self.client.post(reverse('landing_page_clone_url'),
                                data={'url': target})

        soup = BeautifulSoup.BeautifulSoup(resp.content, 'html.parser')
        self.assertIn(POST_DOMAIN, soup.find('form').get('action'))

        real_action = soup.find('input', {'name': 'mercure_real_action_url'})
        self.assertEqual(real_action.get('type'), 'hidden')
        self.assertEqual(real_action.get('value'), 'formaction.php')

        source_url = soup.find('input', {'name': 'mercure_redirect_url'})
        self.assertEqual(source_url.get('type'), 'hidden')
        self.assertEqual(source_url.get('value'), target)

    def test_clone_url_slash_more(self):
        target = 'https://gist.githubusercontent.com/julienlh/' \
                 'f4602caa972ce52dfd67fb92053f7563/raw/' \
                 '82d276da''9ba439f30ed466dbec0619eb74d2e3f8/form4.php'

        url_action = 'http://%s%s' % (
            POST_DOMAIN,
            reverse('landing_page_post', args=[POST_TRACKER_ID]),
        )

        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We first clone a simple site and compare body that must be identical
        requests.get(target)
        cloneresp = self.client.post(reverse('landing_page_clone_url'),
                                     data={'url': target})

        clonesoup = BeautifulSoup.BeautifulSoup(cloneresp.content,
                                                'html.parser')

        # Check that a action tag has been edited
        self.assertEqual(clonesoup.find('form').get('action'), url_action)

    def test_clone_url_point(self):
        target = 'https://gist.githubusercontent.com/julienlh/' \
                 '5ea58bf2984fb1c81512025e35c706fb/raw/' \
                 '4c5486eaaebfb2d3871f5edaf57bbfe7e0bef45e/form3.php'

        url_action = 'http://%s%s' % (
            POST_DOMAIN,
            reverse('landing_page_post', args=[POST_TRACKER_ID]),
        )

        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We first clone a simple site and compare body that must be identical
        requests.get(target)
        cloneresp = self.client.post(reverse('landing_page_clone_url'),
                                     data={'url': target})

        clonesoup = BeautifulSoup.BeautifulSoup(cloneresp.content,
                                                'html.parser')

        # Check that a action tag has been edited
        self.assertEqual(clonesoup.find('form').get('action'), url_action)

    def test_clone_url_slash(self):
        target = 'https://gist.githubusercontent.com/julienlh/' \
                 'd4004343ce0b9406f77e5ccdb63b355a/raw/' \
                 '17b7c8732614fc410b27f5d3f89b456df9ca0b40/form2.php'

        url_action = 'http://%s%s' % (
            POST_DOMAIN,
            reverse('landing_page_post', args=[POST_TRACKER_ID]),
        )

        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We first clone a simple site and compare body that must be identical
        requests.get(target)
        cloneresp = self.client.post(reverse('landing_page_clone_url'),
                                     data={'url': target})

        clonesoup = BeautifulSoup.BeautifulSoup(cloneresp.content,
                                                'html.parser')

        # Check that a action tag has been edited
        self.assertEqual(clonesoup.find('form').get('action'), url_action)

    def test_landing_page_view(self):
        target = 'http://www.simplehtmlguide.com/examples/forms1.html'

        # We create a landing page
        lp = LandingPage.objects.create(
            name='Test delete perm',
            html=clone_url(target)
        )

        et = EmailTemplate.objects.create(
            name='Test landing page view',
            email_subject='foo bar',
            text_content='lorem ipsum',
            landing_page_id=lp.pk,
        )

        # We create a campaign
        camp = Campaign.objects.create(
            email_template_id=et.pk,
            name='Test landing page campaign'
        )
        target_grp = TargetGroup.objects.get(pk=1)
        camp.target_groups_add(target_grp)
        self.assertTrue(camp.send())

        # We check that the trackers has been created with the campaign
        qs = camp.trackers.filter(key='landing_page_open')
        self.assertEqual(qs.count(), 1)
        tracker = qs.first()
        self.assertEqual(tracker.campaign_id, camp.pk)
        self.assertEqual(tracker.value, 'not opened')

        # We go to the landing page
        # The HTTP_HOST is mandatory to generate form "action"
        resp = self.client.get(reverse('landing_page', args=(tracker.uuid,)),
                               HTTP_HOST='foo.com')
        self.assertEqual(resp.status_code, 200)

        # We check that the tracker has beend updated
        tracker = qs.first()
        self.assertEqual(tracker.value, 'opened')
        self.assertContains(resp, 'js/navigator-infos.js')

        # We verify that the landing page
        # has been modified with correct tracker
        soup = BeautifulSoup.BeautifulSoup(resp.content, 'html.parser')
        form = soup.find('form')
        action = form.get('action')
        tracker_post = Tracker.objects.filter(
            campaign_id=camp.pk,
            target_id=1,
            key=TRACKER_LANDING_PAGE_POST
        ).first()
        waited_action = 'http://foo.com%s' % reverse('landing_page_post',
                                                     args=(tracker_post.uuid,))

        self.assertEqual(action, waited_action)

    def test_landing_page_view_invalid_post_id(self):
        target = 'http://www.simplehtmlguide.com/examples/forms1.html'

        # We create a landing page
        lp = LandingPage.objects.create(
            name='Test delete perm',
            html=clone_url(target)
        )

        et = EmailTemplate.objects.create(
            name='Test landing page view',
            email_subject='foo bar',
            text_content='lorem ipsum',
            landing_page_id=lp.pk,
        )

        # We create a campaign
        camp = Campaign.objects.create(
            email_template_id=et.pk,
            name='Test landing page campaign'
        )
        target_grp = TargetGroup.objects.get(pk=1)
        camp.target_groups_add(target_grp)
        self.assertTrue(camp.send())

        # Remove tracker post to see if page load anymore
        Tracker.objects.filter(
            campaign_id=camp.pk,
            target_id=1,
            key=TRACKER_LANDING_PAGE_POST
        ).delete()

        # We go to the landing page
        # The HTTP_HOST is mandatory to generate form "action"
        tracker = camp.trackers.filter(key='landing_page_open').first()
        resp = self.client.get(
            reverse('landing_page', args=(tracker.uuid,)),
            HTTP_HOST='foo.com')
        self.assertEqual(resp.status_code, 200)

        infos = TrackerInfos.objects.get(target_tracker_id=tracker.pk)
        self.assertEqual(infos.raw,
                         'tracker_post_id of %s in unknown' % tracker.pk)

    def test_landing_page_view_exception(self):
        target = 'http://www.simplehtmlguide.com/examples/forms1.html'

        # We create a landing page
        lp = LandingPage.objects.create(
            name='Test delete perm',
            html=clone_url(target)
        )

        et = EmailTemplate.objects.create(
            name='Test landing page view',
            email_subject='foo bar',
            text_content='lorem ipsum',
            landing_page_id=lp.pk,
        )

        # We create a campaign
        camp = Campaign.objects.create(
            email_template_id=et.pk,
            name='Test landing page campaign'
        )
        target_grp = TargetGroup.objects.get(pk=1)
        camp.target_groups_add(target_grp)
        self.assertTrue(camp.send())

        tracker = camp.trackers.filter(key='landing_page_open').first()

        # set incorrect value for make crash
        tracker.campaign_id = 99999999
        tracker.save()

        resp = self.client.get(reverse('landing_page', args=(tracker.uuid,)))

        # Strange behavior, google set multiple redirect.
        # So we can't use "assertRedirect" function
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], 'https://www.google.com/')

    def test_landing_page_post(self):
        target = 'http://www.simplehtmlguide.com/examples/forms1.html'

        # We create a landing page
        lp = LandingPage.objects.create(
            name='Test delete perm',
            html=clone_url(target)
        )

        et = EmailTemplate.objects.create(
            name='Test landing page view',
            email_subject='foo bar',
            text_content='lorem ipsum',
            landing_page_id=lp.pk,
        )

        # We create a campaign
        camp = Campaign.objects.create(
            email_template_id=et.pk,
            name='Test landing page campaign'
        )
        target_grp = TargetGroup.objects.get(pk=1)
        camp.target_groups_add(target_grp)
        self.assertTrue(camp.send())

        tracker_post = Tracker.objects.filter(
            campaign_id=camp.pk,
            target_id=1,
            key=TRACKER_LANDING_PAGE_POST
        ).first()

        data = {
            'username': 'foo',
            'password': 'bar',
            'mercure_real_action_url': 'http://foo.com',
            'mercure_redirect_url': target
        }
        resp = self.client.post(reverse('landing_page_post',
                                        args=(tracker_post.pk,)), data=data)
        self.assertEqual(resp.status_code, 200)

        soup = BeautifulSoup.BeautifulSoup(resp.content, 'html.parser')
        self.assertEqual(soup.find('base').get('href'), target)
        self.assertEqual(soup.find('form').get('action'), 'http://foo.com')

        val = soup.find('input', {'name': 'username'}).get('value')
        self.assertEqual(val, 'foo')

        val = soup.find('input', {'name': 'password'}).get('value')
        self.assertEqual(val, 'bar')

    def test_intercept_html_post(self):

        def _clean_html(html):
            return html.replace('\n', '').replace('\t', '')

        source_url = 'https://sub.example.com/page'
        path = os.path.join(FILES_PATH, 'source_landing_page.html')
        with open(path) as f:
            source_html = _clean_html(f.read())

        # get html valid result
        path = os.path.join(FILES_PATH, 'landing_page_with_form.html')
        with open(path) as f:
            need_html = _clean_html(f.read())

        # test helper
        html_result = intercept_html_post(source_html, source_url)
        self.assertEqual(_clean_html(html_result), need_html)

        # imbricated helper (edit on fist call only)
        html_result = intercept_html_post(source_html, source_url)
        html_result = intercept_html_post(html_result, source_url)
        self.assertEqual(_clean_html(html_result), need_html)

        # test signal
        landing_page = LandingPage.objects.create(
            name='Test intercept html post signal',
            html=source_html
        )
        need = need_html \
            .replace('/page', '') \
            .replace('https://sub.example.com', 'https://www.google.com')
        self.assertEqual(_clean_html(landing_page.html), need)
