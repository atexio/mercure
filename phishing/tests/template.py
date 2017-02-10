import os
from datetime import datetime

from django.test import TestCase
from django.urls import reverse

from phishing.helpers import minimize_url, get_template_vars
from phishing.models import Target, TargetGroup, EmailTemplate
from phishing.tests.constant import FIXTURE_PATH


class TemplateTestCase(TestCase):
    fixtures = [
        os.path.join(FIXTURE_PATH, 'user.json'),
    ]

    def search_var(self, var_list, name):
        result = [v for v in var_list if v.get('name', '') == name]

        self.assertLessEqual(len(result), 1, 'duplicate: %s' % result)
        return result[0] if len(result) else None

    def test_email_template_vars(self):
        target = Target.objects.create(
            email='j.doe@gmail.com',
            first_name='John',
            last_name='Doe',
            group=TargetGroup.objects.create(name='test group')
        )
        var_list = get_template_vars(target=target)

        # email
        var = self.search_var(var_list, 'email')
        self.assertIsNotNone(var)
        self.assertEqual(var['value'], 'j.doe@gmail.com')

        # first name
        var = self.search_var(var_list, 'first_name')
        self.assertIsNotNone(var)
        self.assertEqual(var['value'], 'John')

        # last name
        var = self.search_var(var_list, 'last_name')
        self.assertIsNotNone(var)
        self.assertEqual(var['value'], 'Doe')

    def test_global_vars(self):
        var_list = get_template_vars()
        date = datetime.now()

        # date
        var = self.search_var(var_list, 'date')
        self.assertIsNotNone(var)
        self.assertEqual(var['value'], date.strftime('%d/%m/%Y'))

        # time
        var = self.search_var(var_list, 'time')
        self.assertIsNotNone(var)
        self.assertEqual(var['value'], date.strftime('%H:%M'))

    def test_target_vars(self):
        email_template = EmailTemplate.objects.create(
            name='email template name',
            email_subject='email template subject',
            from_email='from@email.com',
            text_content='content'
        )
        var_list = get_template_vars(email_template=email_template)

        # email subject
        var = self.search_var(var_list, 'email_subject')
        self.assertIsNotNone(var)
        self.assertEqual(var['value'], 'email template subject')

        # from email
        var = self.search_var(var_list, 'from_email')
        self.assertIsNotNone(var)
        self.assertEqual(var['value'], 'from@email.com')

    def test_shortener(self):
        orig_url = 'https://google.fr/whosoawesomepaddingtocreatealongurl'
        res = minimize_url(orig_url)

        self.assertIn('tinyurl.com/', res)

    def test_clone_emailtemplate(self):
        tpl = EmailTemplate.objects.create(
            name='email template name',
            email_subject='email template subject',
            from_email='from@email.com',
            text_content='content',
        )

        # login
        self.client.login(username='admin', password='supertest')

        url = reverse('email_template_clone', args=(tpl.pk,))
        response = self.client.get(url)
        self.assertRedirects(response, reverse('email_template_list'))

        tpl_clone = EmailTemplate.objects.get(name='[Clone] %s' % tpl.name)
        self.assertEqual(tpl_clone.email_subject, tpl.email_subject)
        self.assertEqual(tpl_clone.from_email, tpl.from_email)
        self.assertEqual(tpl_clone.text_content, tpl.text_content)

    def test_clone_emailtemplate_permissions(self):
        tpl = EmailTemplate.objects.create(
            name='email template name',
            email_subject='email template subject',
            from_email='from@email.com',
            text_content='content',
        )

        url = reverse('email_template_clone', args=(tpl.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp['Location'], '%s?next=%s' % (reverse('login'), url))

    def test_add_emailtemplate(self):
        self.client.login(username='admin', password='supertest')

        data = {
            'name': 'Test template add',
            'email_subject': 'Foo bar',
            'from_email': 'foo@test.com',
            'text_content': 'Hello'
        }
        resp = self.client.post(reverse('email_template_add'), data=data)
        self.assertRedirects(resp, reverse('email_template_list'))

        qs = EmailTemplate.objects.filter(name='Test template add')
        self.assertEqual(qs.count(), 1)

        tpl = qs.first()
        self.assertEqual(tpl.email_subject, 'Foo bar')
        self.assertEqual(tpl.from_email, 'foo@test.com')
        self.assertEqual(tpl.text_content, 'Hello')

    def test_add_emailtemplate_permissions(self):
        url = reverse('email_template_add')
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp['Location'], '%s?next=%s' % (reverse('login'), url))

        # We log as admin
        self.client.login(username='admin', password='supertest')

        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)

    def test_edit_emailtemplate(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We create an email template
        tpl = EmailTemplate.objects.create(
            name='Test template add',
            email_subject='Foo bar',
            from_email='foo@test.com',
            text_content='Hello'
        )

        data = {
            'name': 'test name',
            'email_subject': 'test subject',
            'from_email': 'bar@test.com',
            'text_content': 'New Hello'
        }
        resp = self.client.post(reverse('email_template_edit', args=(tpl.pk,)),
                                data=data)
        self.assertRedirects(resp, reverse('email_template_list'))

        # We check that the object is updated in database
        tpl_test = EmailTemplate.objects.get(pk=tpl.pk)
        self.assertEqual(tpl_test.name, 'test name')
        self.assertEqual(tpl_test.email_subject, 'test subject')
        self.assertEqual(tpl_test.from_email, 'bar@test.com')
        self.assertEqual(tpl_test.text_content, 'New Hello')
        self.assertEqual(tpl_test.pk, tpl.pk)

    def test_edit_email_template_permissions(self):
        # We create an email template
        tpl = EmailTemplate.objects.create(
            name='Test template add',
            email_subject='Foo bar',
            from_email='foo@test.com',
            text_content='Hello'
        )

        url = reverse('email_template_edit', args=(tpl.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp['Location'], '%s?next=%s' % (reverse('login'), url))

        # We log as admin
        self.client.login(username='admin', password='supertest')
        resp = self.client.get(reverse('email_template_edit', args=(tpl.pk,)))
        self.assertEqual(resp.status_code, 200)

        # TODO: Test user that is not admin

    def test_delete_email_template(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We create an email template
        tpl = EmailTemplate.objects.create(
            name='Test template add',
            email_subject='Foo bar',
            from_email='foo@test.com',
            text_content='Hello'
        )

        # We remove it and check that it correctly redirect
        resp = self.client.post(reverse('email_template_delete',
                                        args=(tpl.pk,)))
        self.assertRedirects(resp, reverse('email_template_list'))

        # We check that the landing page doesn't exists anymor
        self.assertEqual(EmailTemplate.objects.filter(pk=tpl.pk).count(), 0)

    def test_delete_email_template_permissions(self):
        # We create an email template
        tpl = EmailTemplate.objects.create(
            name='Test template add',
            email_subject='Foo bar',
            from_email='foo@test.com',
            text_content='Hello'
        )

        url = reverse('email_template_delete', args=(tpl.pk,))
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp['Location'], '%s?next=%s' % (reverse('login'), url))

        # We log as admin
        self.client.login(username='admin', password='supertest')
        resp = self.client.get(reverse('email_template_delete',
                                       args=(tpl.pk,)))
        self.assertEqual(resp.status_code, 200)

        # TODO: Test user that is not admin
