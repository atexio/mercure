from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.urls import reverse
from django.test import TestCase

from phishing.models import Campaign, EmailTemplate, TargetGroup, Target


class PermissionTestCase(TestCase):
    def setUp(self):
        super(PermissionTestCase, self).setUp()
        self.client.get('not-found')  # django fix: first client call is 404

    def test_default_permission(self):
        user_infos = {'username': 'default', 'password': 'pass'}
        user = get_user_model().objects.create_user(**user_infos)
        menu = user.get_menu()

        # only campaign list on default
        self.assertEqual(len(menu), 3)

        # check login required
        url = reverse('campaign_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=%s' % url)

        # login
        self.client.login(**user_infos)

        # add test object
        campaign_infos = {
            'email_template': EmailTemplate.objects.create(name='test'),
            'smtp_use_ssl': True,
        }
        campaign = Campaign.objects.create(name='test 1', **campaign_infos)
        Campaign.objects.create(name='test 2', **campaign_infos)
        Campaign.objects.create(name='test 3', **campaign_infos)

        # send campaign
        target_group = TargetGroup.objects.create(name='targets')
        Target.objects.create(email='test@test.com',
                              group=target_group)
        campaign.target_groups_add(target_group)
        self.assertTrue(campaign.send())

        # can list campaign
        response = self.client.get(reverse('campaign_list'))
        content = response.content.decode()
        self.assertEqual(response.status_code, 200)

        # html contain link
        url = reverse('campaign_dashboard', args=(campaign.pk,))
        self.assertIn(url, content)

        # html not contain link
        url = reverse('campaign_delete', args=(campaign.pk,))
        self.assertNotIn(url, content)
        self.assertNotIn(reverse('campaign_add'), content)

        # delete not authorized
        url = reverse('campaign_delete', args=(campaign.pk,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=%s' % url)

        # add not authorized
        url = reverse('campaign_add')
        campaign_infos['name'] = 'test 4'
        response = self.client.post(url, campaign_infos)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, '/accounts/login/?next=%s' % url)

    def test_permission(self):
        permissions = ['view_emailtemplate', 'view_targetgroup']

        for count, name in enumerate(permissions):
            count += 1  # index start to 0

            # add permission
            user, _ = get_user_model().objects.get_or_create(username='perm')
            permission = Permission.objects.get(codename=name)
            user.user_permissions.add(permission)
            self.assertEqual(len(user.get_all_permissions()), count)

            # check user menu
            menu = user.get_menu()
            self.assertEqual(len(menu), 3 + count)

    def test_print_user(self):
        user, _ = get_user_model().objects.get_or_create(username='perm')
        self.assertEqual(user.__str__(), 'perm')
