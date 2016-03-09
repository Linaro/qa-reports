from django_dynamic_fixture import G

from django.test import TestCase
from django.contrib.auth import get_user_model

from reports import models


User = get_user_model()


class TestPermissions(TestCase):

    def test_allow_all(self):
        G(models.TestJob)
        G(models.TestJob)

        user = G(User)

        results = models.Permission.ACL(user, models.TestJob.objects.all())

        self.assertEqual(results.count(), 2)

    def test_private_1(self):
        G(models.TestJob, private=True)
        G(models.TestJob, private=True)

        user = G(User)

        results = models.Permission.ACL(user, models.TestJob.objects.all())

        self.assertEqual(results.count(), 0)

    def test_private_2(self):
        G(models.TestJob, private=False)
        G(models.TestJob, private=True)

        user = G(User)

        results = models.Permission.ACL(user, models.TestJob.objects.all())

        self.assertEqual(results.count(), 1)

    def test_permission_1(self):
        G(models.TestJob, test_execution__branch='test_1', private=True)
        G(models.TestJob, test_execution__branch='test_2', private=True)

        user = G(User)

        G(models.Permission, user=user, field='test_execution__branch', value='test_1')
        G(models.Permission, user=user, field='test_execution__branch', value='test_2')

        results = models.Permission.ACL(user, models.TestJob.objects.all())

        self.assertEqual(results.count(), 2)

    def test_permission_2(self):
        G(models.TestJob)
        G(models.TestJob, test_execution__branch='test_1', private=True)
        G(models.TestJob, test_execution__branch='test_2', private=True)

        user = G(User)

        G(models.Permission, user=user, field='test_execution__branch', value='test_1')
        G(models.Permission, user=user, field='test_execution__branch', value='test_2')

        results = models.Permission.ACL(user, models.TestJob.objects.all())

        self.assertEqual(results.count(), 3)

    def test_permission_super_user(self):
        G(models.TestJob, private=True)
        G(models.TestJob, private=True)

        user = G(User, is_superuser=True)

        results = models.Permission.ACL(user, models.TestJob.objects.all())

        self.assertEqual(results.count(), 2)
