import os

from django.urls import reverse
from django.test import TestCase

from phishing.models import Target
from phishing.models import TargetGroup
from phishing.tests.constant import FIXTURE_PATH


class TargetTestCase(TestCase):
    fixtures = [
        os.path.join(FIXTURE_PATH, 'user.json'),
    ]

    def test_form_target_invalid_name(self):
        self.client.login(username='admin', password='supertest')

        # Check invalid form
        response = self.client.post(reverse("target_group_add"),
                                    {
                                        'name': '',
                                        'targets-0-DELETE': None,
                                        'targets-0-email': 'test@test.com',
                                        'targets-0-first_name': None,
                                        'targets-0-id': None,
                                        'targets-0-last_name': None,
                                        'targets-INITIAL_FORMS': 0,
                                        'targets-MAX_NUM_FORMS': 1000,
                                        'targets-MIN_NUM_FORMS': 0,
                                        'targets-TOTAL_FORMS': 2,
                                    })

        targetGroup = TargetGroup.objects.filter(name='OLOL').first()
        self.assertIsNone(targetGroup)
        self.assertEqual(response.status_code, 200)
        target = Target.objects.filter(email='test').first()
        self.assertIsNone(target)

    def test_form_target_invalid_email(self):
        self.client.login(username='admin', password='supertest')

        # Check invalid form
        response = self.client.post(reverse("target_group_add"),
                                    {
                                        'name': 'OLOLTEST',
                                        'targets-0-DELETE': '',
                                        'targets-0-email': 'lol',
                                        'targets-0-first_name': '',
                                        'targets-0-id': '',
                                        'targets-0-last_name': '',
                                        'targets-INITIAL_FORMS': 0,
                                        'targets-MAX_NUM_FORMS': 1000,
                                        'targets-MIN_NUM_FORMS': 0,
                                        'targets-TOTAL_FORMS': 1,
                                    })

        targetGroup = TargetGroup.objects.filter(name='OLOLTEST').first()
        self.assertIsNone(targetGroup)
        self.assertEqual(response.status_code, 200)
        target = Target.objects.filter(email='lol').first()
        self.assertIsNone(target)

    def test_form_target_valid(self):
        self.client.login(username='admin', password='supertest')

        response = self.client.post(reverse("target_group_add"),
                                    {
                                        'name': 'OLOL',
                                        'targets-0-DELETE': None,
                                        'targets-0-email': 'test@test.com',
                                        'targets-0-first_name': None,
                                        'targets-0-id': None,
                                        'targets-0-last_name': None,
                                        'targets-INITIAL_FORMS': 0,
                                        'targets-MAX_NUM_FORMS': 1000,
                                        'targets-MIN_NUM_FORMS': 0,
                                        'targets-TOTAL_FORMS': 1,
                                    },
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        targetGroup = TargetGroup.objects.filter(name='OLOL').first()
        self.assertEqual(targetGroup.name, 'OLOL')
        self.assertRedirects(response, reverse('target_group_list'))
        target = Target.objects.filter(email='test').first()
        self.assertIsNone(target)

    def test_print_target(self):
        self.client.login(username='admin', password='supertest')

        self.client.post(reverse("target_group_add"),
                         {
                             'name': 'OLOL',
                             'targets-0-DELETE': None,
                             'targets-0-email': 'test@test.com',
                             'targets-0-first_name': None,
                             'targets-0-id': None,
                             'targets-0-last_name': None,
                             'targets-INITIAL_FORMS': 0,
                             'targets-MAX_NUM_FORMS': 1000,
                             'targets-MIN_NUM_FORMS': 0,
                             'targets-TOTAL_FORMS': 1,
                         },
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        targetGroup = TargetGroup.objects.filter(name='OLOL').first()
        self.assertEqual(targetGroup.__str__(), 'OLOL')

    def test_form_target_edit(self):
        self.client.login(username='admin', password='supertest')

        self.client.post(reverse("target_group_add"),
                         {
                             'name': 'OLOL',
                             'targets-0-DELETE': None,
                             'targets-0-email': 'test@test.com',
                             'targets-0-first_name': None,
                             'targets-0-id': None,
                             'targets-0-last_name': None,
                             'targets-INITIAL_FORMS': 0,
                             'targets-MAX_NUM_FORMS': 1000,
                             'targets-MIN_NUM_FORMS': 0,
                             'targets-TOTAL_FORMS': 1,
                         },
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        targetGroup = TargetGroup.objects.filter(name='OLOL').first()

        response = self.client.post(reverse("target_group_edit",
                                            args=(targetGroup.pk,)),
                                    {
                                        'name': 'OLOLOL',
                                        'targets-0-DELETE': None,
                                        'targets-0-email': 'foo@test.com',
                                        'targets-0-first_name': None,
                                        'targets-0-id': None,
                                        'targets-0-last_name': None,
                                        'targets-INITIAL_FORMS': 0,
                                        'targets-MAX_NUM_FORMS': 1000,
                                        'targets-MIN_NUM_FORMS': 0,
                                        'targets-TOTAL_FORMS': 1,
                                    },
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        targetGroup = TargetGroup.objects.filter(name='OLOLOL').first()
        self.assertEqual(targetGroup.name, 'OLOLOL')
        self.assertRedirects(response, reverse('target_group_list'))

        self.assertIsNone(TargetGroup.objects.filter(name='OLOL').first())

        target = Target.objects.filter(email='test').first()
        self.assertIsNone(target)

    def test_form_target_delete(self):
        self.client.login(username='admin', password='supertest')

        self.client.post(reverse("target_group_add"),
                         {
                             'name': 'OLOL',
                             'targets-0-DELETE': None,
                             'targets-0-email': 'test@test.com',
                             'targets-0-first_name': None,
                             'targets-0-id': None,
                             'targets-0-last_name': None,
                             'targets-INITIAL_FORMS': 0,
                             'targets-MAX_NUM_FORMS': 1000,
                             'targets-MIN_NUM_FORMS': 0,
                             'targets-TOTAL_FORMS': 1,
                         },
                         HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        targetGroup = TargetGroup.objects.filter(name='OLOL').first()
        self.client.post(reverse("target_group_delete",
                                 args=(targetGroup.pk,)))
        self.assertIsNone(TargetGroup.objects.filter(name='OLOL').first())

        target = Target.objects.filter(email='test').first()
        self.assertIsNone(target)
