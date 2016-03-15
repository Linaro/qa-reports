from mock import patch
from django.test import TestCase
from django.contrib.auth.models import User, Group

from crowd.backend import CrowdBackend


class TestCrowdSyncUserBackend(TestCase):

    data = {u'active': False,
            u'email': 'things@gmail.com',
            u'first-name': 'test1',
            u'last-name': 'test2'}

    @patch('crowd.AUTH_CROWD_ALWAYS_UPDATE_USER', True)
    @patch('crowd.backend.CrowdBackend.crowd_user')
    def test_sync_user_1(self, crowd_user):
        crowd_user.return_value = self.data
        user = User.objects.create(username="test1")

        CrowdBackend().sync_user(user)

        self.assertEqual(user.is_active, False)
        self.assertEqual(user.email, 'things@gmail.com')
        self.assertEqual(user.first_name, 'test1')
        self.assertEqual(user.last_name, 'test2')

    @patch('crowd.AUTH_CROWD_ALWAYS_UPDATE_USER', False)
    @patch('crowd.backend.CrowdBackend.crowd_user')
    def test_sync_user_2(self, crowd_user):
        crowd_user.return_value = self.data

        user = User.objects.create(username="test2")

        CrowdBackend().sync_user(user)

        self.assertEqual(user.is_active, True)
        self.assertEqual(user.email, '')
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, '')


class TestCrowdSyncGroupsBackend(TestCase):

    data = {'groups': [
        {u'name': u'admins'},
        {u'name': u'users'}]
    }

    @patch('crowd.AUTH_CROWD_ALWAYS_UPDATE_GROUPS', True)
    @patch('crowd.backend.CrowdBackend.crowd_get_groups')
    def test_set_groups_1(self, crowd_get_groups):
        crowd_get_groups.return_value = self.data
        user = User.objects.create(username="test")

        users = Group.objects.create(name="users")
        admins = Group.objects.create(name="admins")
        other = Group.objects.create(name="other")

        CrowdBackend().sync_groups(user)

        self.assertEqual(user.groups.count(), 2)
        self.assertTrue(users in user.groups.all())
        self.assertTrue(admins in user.groups.all())
        self.assertTrue(other not in user.groups.all())

    @patch('crowd.AUTH_CROWD_ALWAYS_UPDATE_GROUPS', False)
    @patch('crowd.backend.CrowdBackend.crowd_get_groups')
    def test_set_groups_2(self, crowd_get_groups):
        crowd_get_groups.return_value = self.data
        user = User.objects.create(username="test")

        Group.objects.create(name="users")
        Group.objects.create(name="admins")

        CrowdBackend().sync_groups(user)

        self.assertEqual(user.groups.count(), 0)

    @patch('crowd.AUTH_CROWD_ALWAYS_UPDATE_GROUPS', True)
    @patch('crowd.AUTH_CROWD_GROUP_MAP', {'admins': 'gods'})
    @patch('crowd.backend.CrowdBackend.crowd_get_groups')
    def test_set_groups_map(self, crowd_get_groups):
        crowd_get_groups.return_value = self.data
        user = User.objects.create(username="test")

        gods = Group.objects.create(name="gods")

        CrowdBackend().sync_groups(user)

        self.assertEqual(user.groups.count(), 1)
        self.assertTrue(gods in user.groups.all())

    @patch('crowd.AUTH_CROWD_ALWAYS_UPDATE_GROUPS', True)
    @patch('crowd.AUTH_CROWD_SUPERUSER_GROUP', 'admins')
    @patch('crowd.backend.CrowdBackend.crowd_get_groups')
    def test_set_groups_superuser(self, crowd_get_groups):
        crowd_get_groups.return_value = self.data
        user = User.objects.create(username="test")
        Group.objects.create(name="admins")
        CrowdBackend().sync_groups(user)

        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.is_superuser, True)

    @patch('crowd.AUTH_CROWD_ALWAYS_UPDATE_GROUPS', True)
    @patch('crowd.AUTH_CROWD_STAFF_GROUP', 'users')
    @patch('crowd.backend.CrowdBackend.crowd_get_groups')
    def test_set_groups_staff(self, crowd_get_groups):
        crowd_get_groups.return_value = self.data
        user = User.objects.create(username="test")
        Group.objects.create(name="users")
        CrowdBackend().sync_groups(user)

        self.assertEqual(user.groups.count(), 1)
        self.assertEqual(user.is_staff, True)

    @patch('crowd.AUTH_CROWD_ALWAYS_UPDATE_GROUPS', True)
    @patch('crowd.AUTH_CROWD_CREATE_GROUPS', True)
    @patch('crowd.backend.CrowdBackend.crowd_get_groups')
    def test_set_groups_create(self, crowd_get_groups):
        crowd_get_groups.return_value = self.data
        user = User.objects.create(username="test")
        CrowdBackend().sync_groups(user)

        self.assertEqual(user.groups.count(), 2)
        self.assertTrue('admins' in user.groups.values_list('name', flat=True))
        self.assertTrue('users' in user.groups.values_list('name', flat=True))
