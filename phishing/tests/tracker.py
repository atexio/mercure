import os
import random
import uuid
from string import ascii_lowercase
from django.test import TestCase
from django.urls import reverse

from phishing.models import Campaign, Tracker, TrackerInfos, TargetGroup, \
    Target
from phishing.tests.constant import FIXTURE_PATH


class TrackerTestCase(TestCase):
    fixtures = [
        os.path.join(FIXTURE_PATH, 'landing_page.json'),
        os.path.join(FIXTURE_PATH, 'target.json'),
        os.path.join(FIXTURE_PATH, 'template.json'),
        os.path.join(FIXTURE_PATH, 'user.json'),
    ]

    def test_browser_tracker(self):
        camp = Campaign.objects.create(
            email_template_id=1,
            name='Browser tracker test'
        )
        camp.target_groups_add(
            TargetGroup.objects.first()
        )

        tracker = Tracker.objects.create(
            campaign_id=camp.pk,
            target_id=Target.objects.first().pk
        )
        infos = TrackerInfos.objects.create(
            target_tracker_id=tracker.pk,
        )

        self.client.login(username='admin', password='supertest')

        # Test with wrong post data
        r = self.client.post(reverse('tracker_set_infos',
                                     args=(tracker.uuid,)),
                             data={'foo': 'bar'})
        self.assertEqual(r.status_code, 400)

        # Test with a wrong tracker ID
        r = self.client.post(reverse('tracker_set_infos',
                                     args=(uuid.uuid4(),)),
                             data={'infos': 'test'})
        self.assertEqual(r.status_code, 404)

        # Test with valid infos
        randinf = ''.join(random.choice(ascii_lowercase) for _ in range(10))
        r = self.client.post(reverse('tracker_set_infos',
                                     args=(tracker.uuid,)),
                             data={'infos': randinf})
        self.assertEqual(TrackerInfos.objects.get(pk=infos.pk).raw, randinf)
        self.assertEqual(r.status_code, 200)

        # Test repost with the same uuid
        r = self.client.post(reverse('tracker_set_infos',
                                     args=(tracker.uuid,)),
                             data={'infos': 'foo'})
        self.assertEqual(r.status_code, 404)
        self.assertEqual(TrackerInfos.objects.get(pk=infos.pk).raw, randinf)

    def test_image_tracker(self):
        camp = Campaign.objects.create(
            email_template_id=1,
            name='Browser tracker test'
        )
        camp.target_groups_add(
            TargetGroup.objects.first()
        )

        tracker = Tracker.objects.create(
            campaign_id=camp.pk,
            target_id=Target.objects.first().pk
        )

        self.client.login(username='admin', password='supertest')

        # Test with a wrong uuid
        resp = self.client.post(reverse('tracker_img', args=(uuid.uuid4(),)))
        self.assertEqual(resp.status_code, 404)

        # Test with a valid uuid
        resp = self.client.post(reverse('tracker_img', args=(tracker.uuid,)))
        self.assertEqual(resp.status_code, 200)

        tracker = Tracker.objects.get(pk=tracker.pk)
        self.assertEqual(tracker.infos, '1')

        infos = TrackerInfos.objects.filter(target_tracker_id=tracker.pk)
        self.assertEqual(infos.count(), 1)
        first_infos = infos.first()
        self.assertEqual(first_infos.referer, None)
        self.assertEqual(first_infos.ip, '127.0.0.1')
        self.assertEqual(first_infos.user_agent, None)

        # Test a second opening
        resp = self.client.post(reverse('tracker_img', args=(tracker.uuid,)))
        self.assertEqual(resp.status_code, 200)

        tracker = Tracker.objects.get(pk=tracker.pk)
        self.assertEqual(tracker.infos, '2')

        infos = TrackerInfos.objects.filter(target_tracker_id=tracker.pk)
        self.assertEqual(infos.count(), 2)

    def test_print_tracker(self):
        camp = Campaign.objects.create(
            email_template_id=1,
            name='Browser tracker test'
        )
        camp.target_groups_add(
            TargetGroup.objects.first()
        )

        Tracker.objects.create(
            campaign_id=camp.pk,
            target_id=Target.objects.first().pk
        )

        self.client.login(username='admin', password='supertest')

        # Test __str__
        self.assertEqual(camp.trackers.all()[0].__str__(),
                         "[Browser tracker test] test@atexio.fr (: )")

    def test_trackerInfo(self):
        camp = Campaign.objects.create(
            email_template_id=1,
            name='Browser tracker test'
        )
        camp.target_groups_add(TargetGroup.objects.first())

        Tracker.objects.create(
            campaign_id=camp.pk,
            target_id=Target.objects.first().pk
        )

        self.client.login(username='admin', password='supertest')

        met = meta('Mozilla', 'www.google.com', '8.8.8.8')
        TrackerInfos.create(target_tracker=camp.trackers.first(),
                            http_request=req(met))

    def test_print_trackerInfo(self):
        camp = Campaign.objects.create(
            email_template_id=1,
            name='Browser tracker test'
        )
        camp.target_groups_add(
            TargetGroup.objects.first()
        )

        Tracker.objects.create(
            campaign_id=camp.pk,
            target_id=Target.objects.first().pk
        )

        self.client.login(username='admin', password='supertest')

        met = meta('Mozilla', 'www.google.com', '8.8.8.8')
        tracker_infos = TrackerInfos.create(
            target_tracker=camp.trackers.first(),
            http_request=req(met))
        # Test __str__
        self.assertEqual(tracker_infos.__str__(),
                         "[Browser tracker test] test@atexio.fr (: )")


# TODO: A supprimer lorsque la méthode "create" sera surchargée
# TODO: Ligne 86 : Remplacer "TrackerInfos.objects.create"
#  avec comme paramètre HttpRequest()
class req:
    def __init__(self, META):
        self.META = META


class meta:
    def __init__(self, user_agent, http_referer, ip):
        self.HTTP_USER_AGENT = user_agent
        self.HTTP_REFERER = http_referer
        self.HTTP_X_FORWARDED_FOR = ip

    def get(self, varName, useless=None):
        if varName == 'HTTP_USER_AGENT':
            return self.HTTP_USER_AGENT
        if varName == 'HTTP_REFERER':
            return self.HTTP_REFERER
        if varName == 'HTTP_X_FORWARDED_FOR':
            return self.HTTP_X_FORWARDED_FOR
