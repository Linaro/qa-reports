from mock import patch

from django_dynamic_fixture import G
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import override_settings

from rest_framework import status
from rest_framework.test import APITestCase

from reports import models

ACCESS_GROUP = "access_group"
EDIT_GROUP = "edit_group"


class TestUser(APITestCase):

    def test_get_1(self):
        response = self.client.get('/api/user/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_2(self):
        user = G(get_user_model(), username="tripbit")
        self.client.force_authenticate(user=user)

        response = self.client.get('/api/user/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'tripbit')


class TestTestJob(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=G(get_user_model(), is_superuser=True))

    def test_create(self):
        mock_test = {
            'some_test_1.yaml': {'steps': [], 'expected': []},
            'some_test_2.yaml': {'steps': [], 'expected': []}
        }

        data = {"tests": ["some_test_1.yaml", "some_test_2.yaml"]}

        definition = G(models.Definition, kind=models.Definition.MANUAL, data=data)
        test_execution = G(models.TestExecution)

        with patch('reports.miner.manual.tests') as miner_tests:
            miner_tests.return_value = mock_test

            data = {
                "definition": definition.id,
                "test_execution": test_execution.id
            }
            response = self.client.post('/api/test-job/', data, format='json')

            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(models.TestJob.objects.count(), 1)
            self.assertEqual(models.RunDefinition.objects.count(), 1)
            self.assertEqual(models.TestResult.objects.count(), 2)

    def test_get_with_results(self):
        test_job = G(models.TestJob, kind="automatic")
        G(models.TestResult, test_job=test_job, name="things/with/urls1.yaml")
        G(models.TestResult, test_job=test_job, name="things/with/urls2.yaml")

        response = self.client.get('/api/test-job/%s/' % test_job.pk)

        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_notes(self):
        test_job = G(models.TestJob, kind='automatic')

        data = {'notes': 'a text'}
        url = '/api/test-job/%s/' % test_job.id

        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.TestJob.objects.get().notes, data['notes'])


@override_settings(ACCESS_GROUP=ACCESS_GROUP)
class TestTestJobPermission(APITestCase):

    def test_get_with_permissions_1(self):
        G(models.TestJob, private=True)
        G(models.TestJob, private=True)

        user = G(get_user_model(), groups=[G(Group, name=ACCESS_GROUP)])

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/test-job/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_with_permissions_2(self):
        G(models.TestJob, private=False)
        G(models.TestJob, private=False)

        user = G(get_user_model(), groups=[G(Group, name=ACCESS_GROUP)])

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/test-job/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_get_with_permissions_3(self):
        G(models.TestJob, test_execution__branch='test_1', private=True, kind="automatic")
        G(models.TestJob, test_execution__branch='test_2', private=True, kind="automatic")

        user = G(get_user_model(), groups=[G(Group, name=ACCESS_GROUP)])

        G(models.Permission, user=user, field='test_execution__branch', value='test_1')
        G(models.Permission, user=user, field='test_execution__branch', value='test_2')

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/test-job/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)


@override_settings(ACCESS_GROUP=ACCESS_GROUP)
@override_settings(EDIT_GROUP=EDIT_GROUP)
class TestResult(APITestCase):

    def setUp(self):
        access_group = G(Group, name=ACCESS_GROUP)
        edit_group = G(Group, name=EDIT_GROUP)

        self.user_1 = G(get_user_model(), name="tripbit1", groups=[
            access_group, edit_group
        ])
        self.user_2 = G(get_user_model(), name="tripbit2", groups=[
            access_group, edit_group
        ])

    def test_read(self):
        test_result = G(models.TestResult, name="things/with/urls.yaml")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        self.client.force_authenticate(user=self.user_1)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_1(self):
        test_result = G(models.TestResult, name="things/with/urls.yaml")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        data = {'status': 'pass'}

        self.client.force_authenticate(user=self.user_1)

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_result = models.TestResult.objects.get()

        self.assertEqual(test_result.status, 'pass')
        self.assertEqual(test_result.modified_by, self.user_1)

    def test_update_2(self):
        test_result = G(models.TestResult, name="things/with/urls.yaml")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        data = {'status': None}

        self.client.force_authenticate(user=self.user_1)

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_result = models.TestResult.objects.get()

        self.assertEqual(test_result.status, None)
        self.assertEqual(test_result.modified_by, None)

    def test_update_3(self):
        original_name = "things/with/urls.yaml"
        test_result = G(models.TestResult, name=original_name)
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        data = {'status': 'pass', 'name': 'things'}

        self.client.force_authenticate(user=self.user_1)

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.TestResult.objects.get().status, 'pass')
        self.assertEqual(models.TestResult.objects.get().name, original_name)

    def test_update_collision_1(self):
        test_result = G(models.TestResult, name="test_name")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        modified_at = test_result.modified_at.strftime("%H:%M:%S %d-%m-%Y.%f")
        data = {'status': 'pass', 'modified_at': modified_at}

        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=self.user_2)

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_collision_2(self):
        test_result = G(models.TestResult, name="test_name")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        modified_at = test_result.modified_at.strftime("%H:%M:%S %d-%m-%Y.%f")

        data = {'status': 'pass', 'modified_at': modified_at}
        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {'status': 'fail', 'modified_at': modified_at}
        self.client.force_authenticate(user=self.user_2)
        response = self.client.put(url, data, format='json')

        self.assertTrue(response.data['old_status'][0], 'pass')
        self.assertTrue(response.data['new_status'][0], 'fail')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_collision_3(self):
        test_result = G(models.TestResult, name="test_name")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        modified_at = test_result.modified_at.strftime("%H:%M:%S %d-%m-%Y.%f")

        data = {'status': 'pass', 'modified_at': modified_at}
        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {'status': 'fail', 'modified_at': modified_at}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_collision_4(self):
        test_result = G(models.TestResult, name="test_name")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        data = {'status': 'pass'}
        self.client.force_authenticate(user=self.user_1)
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {'status': 'fail'}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_notes(self):
        test_result = G(models.TestResult, name="test_name")

        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)
        data = {'notes': 'a text'}
        self.client.force_authenticate(user=self.user_1)
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.TestResult.objects.get().notes, data['notes'])


class TestIssue(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=G(get_user_model(), is_superuser=True))

    def test_create_bad_kind(self):
        test_result = G(models.TestResult, name="test-1")

        data = {
            'kind': "i don't exist",
            "number": "1",
            "test_result": test_result.id
        }

        response = self.client.post('/api/issue/', data, format='json')

        self.assertTrue('kind' in response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(models.Issue.objects.count(), 0)


class TestIssueKind(APITestCase):

    def setUp(self):
        self.client.force_authenticate(user=G(get_user_model(), is_superuser=True))

    def test_get(self):
        response = self.client.get('/api/issue-kind/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data[0],
                         {'verbose_name': 'GitHub/kernelci', 'name': 'kernelci'})
        self.assertEqual(response.data[1],
                         {'verbose_name': 'Bugzilla/linaro', 'name': 'linaro'})
        self.assertEqual(response.data[2],
                         {'verbose_name': 'Bugzilla/96boards', 'name': '96boards'})
