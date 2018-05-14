import json
import os

from shutil import copyfile

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from phishing.models import Attachment, Tracker
from phishing.strings import TRACKER_ATTACHMENT_EXECUTED
from phishing.tests.constant import FILES_PATH, FIXTURE_PATH


class AttachmentTestCase(TestCase):

    fixtures = [
        os.path.join(FIXTURE_PATH, 'target.json'),
        os.path.join(FIXTURE_PATH, 'user.json'),
    ]

    def test_build(self):
        attachment_name = 'build.json'
        attachment_path = os.path.join(settings.MEDIA_ROOT, 'test_attachment')
        copyfile(os.path.join(FILES_PATH, 'archive.zip'), attachment_path)
        attachment = Attachment(
            name=attachment_name,
            buildable=True
        )
        attachment.file = os.path.join('..', attachment_path)
        attachment.save()

        kwargs = {
            'key': TRACKER_ATTACHMENT_EXECUTED,
            'campaign_id': 1,
            'target_id': 1,
            'value': 'tracker: not opened',
        }
        tracker = Tracker.objects.create(**kwargs)

        res = attachment.build(tracker)
        received = json.loads(res.read().decode())

        tracker_url = 'http://localhost/en/tracker/%s.png' % tracker.pk
        self.assertEqual(received['tracker_url'], tracker_url)
        self.assertEqual(received['target_email'], 'test@atexio.fr')
        self.assertEqual(received['target_first_name'], 'John')
        self.assertEqual(received['target_last_name'], 'Doe')

        # Clean media dir after test
        os.remove(attachment_path)

    def test_build_invalid_zip(self):
        attachment_name = 'build.json'
        attachment_path = os.path.join(settings.MEDIA_ROOT, 'test_attachment')
        copyfile(os.path.join(FILES_PATH, 'invalid_archive.zip'),
                 attachment_path)
        attachment = Attachment(
            name=attachment_name,
            buildable=True
        )
        attachment.file = os.path.join('..', attachment_path)
        attachment.save()

        kwargs = {
            'key': TRACKER_ATTACHMENT_EXECUTED,
            'campaign_id': 1,
            'target_id': 1,
            'value': 'tracker: not opened',
        }
        tracker = Tracker.objects.create(**kwargs)
        with self.assertRaises(SuspiciousOperation):
            attachment.build(tracker)

    def test_build_static(self):
        attachment_name = 'b64.png'
        attachment_path = os.path.join(settings.MEDIA_ROOT, 'test_attachment')
        copyfile(os.path.join(FILES_PATH, 'image.png'), attachment_path)
        attachment = Attachment(
            name=attachment_name,
            buildable=False
        )
        attachment.file = os.path.join('..', attachment_path)
        attachment.save()

        kwargs = {
            'key': TRACKER_ATTACHMENT_EXECUTED,
            'campaign_id': 1,
            'target_id': 1,
            'value': 'tracker: not opened',
        }
        tracker = Tracker.objects.create(**kwargs)

        res = attachment.build(tracker)
        self.assertEqual(res, attachment.file)

        # Clean media dir after test
        os.remove(attachment_path)

    def test_add_attachment(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        data = {
            'name': 'Test attachment',
            'attachment_name': 'foo.txt',
            'buildable': False,
            'file': SimpleUploadedFile('test.txt', b'toto')
        }
        resp = self.client.post(reverse('attachment_add'), data=data)
        self.assertRedirects(resp, reverse('attachment_list'))

        qs = Attachment.objects.filter(name='Test attachment')
        self.assertEqual(qs.count(), 1)

        attachment = qs.first()
        self.assertEqual(attachment.attachment_name, 'foo.txt')
        self.assertEqual(attachment.buildable, False)

    def test_add_attachment_permissions(self):
        resp = self.client.get(reverse('attachment_add'))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, '%s?next=%s' % (reverse('login'),
                                                reverse('attachment_add')))

        # We log as admin
        self.client.login(username='admin', password='supertest')
        resp = self.client.get(reverse('attachment_add'))
        self.assertEqual(resp.status_code, 200)

        # TODO: Test user that is not admin

    def test_edit_attachment(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We create an attachment
        att = Attachment.objects.create(
            name='Test attachment',
            attachment_name='foo.txt',
            buildable=False,
            file=SimpleUploadedFile('test.txt', b'toto')
        )

        # We update attachment with new values
        data = {
            'name': 'Test edit attachment',
            'attachment_name': 'bar.txt',
            'buildable': True,
            'file': SimpleUploadedFile('test.txt', b'tata')
        }
        resp = self.client.post(reverse('attachment_edit', args=(att.pk,)),
                                data=data)
        self.assertRedirects(resp, reverse('attachment_list'))

        # We check that the object is updated in database
        att_edit = Attachment.objects.get(pk=att.pk)
        self.assertEqual(att_edit.name, 'Test edit attachment')
        self.assertEqual(att_edit.attachment_name, 'bar.txt')
        self.assertEqual(att_edit.buildable, True)
        self.assertEqual(att_edit.file.read(), b'tata')
        self.assertEqual(att_edit.pk, att.pk)

    def test_edit_attachment_permissions(self):
        # We create an attachment
        att = Attachment.objects.create(
            name='Test attachment',
            attachment_name='foo.txt',
            buildable=False,
            file=SimpleUploadedFile('test.txt', b'toto')
        )

        # We try to access edit page
        resp = self.client.get(reverse('attachment_edit', args=(att.pk,)))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, '%s?next=%s' % (reverse('login'),
                                                reverse('attachment_edit',
                                                        args=(att.pk,))))

        # We log as admin
        self.client.login(username='admin', password='supertest')
        resp = self.client.get(reverse('attachment_edit', args=(att.pk,)))
        self.assertEqual(resp.status_code, 200)

        # TODO: Test user that is not admin

    def test_delete_attachment(self):
        # We log as admin
        self.client.login(username='admin', password='supertest')

        # We create an attachment
        att = Attachment.objects.create(
            name='Test attachment',
            attachment_name='foo.txt',
            buildable=False,
            file=SimpleUploadedFile('test.txt', b'toto')
        )

        # We remove it and check that it correctly redirect
        resp = self.client.post(reverse('attachment_delete', args=(att.pk,)))
        self.assertRedirects(resp, reverse('attachment_list'))

        # We check that the landing page doesn't exists anymor
        self.assertEqual(Attachment.objects.filter(pk=att.pk).count(), 0)

    def test_delete_attachment_permissions(self):
        # We create an attachment
        att = Attachment.objects.create(
            name='Test attachment',
            attachment_name='foo.txt',
            buildable=False,
            file=SimpleUploadedFile('test.txt', b'toto')
        )

        # We try to access edit page
        resp = self.client.get(reverse('attachment_delete', args=(att.pk,)))
        self.assertEqual(resp.status_code, 302)
        self.assertIn(resp.url, '%s?next=%s' % (reverse('login'),
                                                reverse('attachment_delete',
                                                        args=(att.pk,))))

        # We log as admin
        self.client.login(username='admin', password='supertest')
        resp = self.client.get(reverse('attachment_delete', args=(att.pk,)))
        self.assertEqual(resp.status_code, 200)

        # TODO: Test user that is not admin
