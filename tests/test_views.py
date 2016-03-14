from mock import patch

from django_dynamic_fixture import G
from django.contrib.auth import get_user_model

from rest_framework.test import APITestCase
from rest_framework import status

from reports import models


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

            self.client.force_authenticate(user=G(get_user_model()))
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

    def test_get_with_permissions_1(self):
        G(models.TestJob, private=True)
        G(models.TestJob, private=True)

        response = self.client.get('/api/test-job/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_with_permissions_2(self):
        G(models.TestJob, private=True)
        G(models.TestJob, private=True)

        user = G(get_user_model())

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/test-job/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)

    def test_get_with_permissions_3(self):
        G(models.TestJob, test_execution__branch='test_1', private=True, kind="automatic")
        G(models.TestJob, test_execution__branch='test_2', private=True, kind="automatic")

        user = G(get_user_model())

        G(models.Permission, user=user, field='test_execution__branch', value='test_1')
        G(models.Permission, user=user, field='test_execution__branch', value='test_2')

        self.client.force_authenticate(user=user)
        response = self.client.get('/api/test-job/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)

    def test_update_notes(self):
        test_job = G(models.TestJob, kind='automatic')

        data = {'notes': 'a text'}
        url = '/api/test-job/%s/' % test_job.id

        self.client.force_authenticate(user=G(get_user_model()))
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.TestJob.objects.get().notes, data['notes'])


class TestResult(APITestCase):

    def setUp(self):
        self.user = G(get_user_model(), username="tripbit")
        self.client.force_authenticate(user=self.user)

    def test_read(self):
        test_result = G(models.TestResult, name="things/with/urls.yaml")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_1(self):
        test_result = G(models.TestResult, name="things/with/urls.yaml")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        data = {'status': 'pass'}

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        test_result = models.TestResult.objects.get()

        self.assertEqual(test_result.status, 'pass')
        self.assertEqual(test_result.modified_by, self.user)

    def test_update_2(self):
        original_name = "things/with/urls.yaml"
        test_result = G(models.TestResult, name=original_name)
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        data = {'status': 'pass', 'name': 'things'}

        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(models.TestResult.objects.get().status, 'pass')
        self.assertEqual(models.TestResult.objects.get().name, original_name)

    def test_update_collision_1(self):
        test_result = G(models.TestResult, name="test_name")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        modified_at = test_result.modified_at.strftime("%H:%M:%S %d-%m-%Y.%f")
        data = {'status': 'pass', 'modified_at': modified_at}

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user = G(get_user_model(), username="tripbit2")
        self.client.force_authenticate(user=self.user)

        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_collision_2(self):
        test_result = G(models.TestResult, name="test_name")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        modified_at = test_result.modified_at.strftime("%H:%M:%S %d-%m-%Y.%f")

        data = {'status': 'pass', 'modified_at': modified_at}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user = G(get_user_model(), username="tripbit2")
        self.client.force_authenticate(user=self.user)

        data = {'status': 'fail', 'modified_at': modified_at}
        response = self.client.put(url, data, format='json')

        self.assertTrue(response.data['old_status'][0], 'pass')
        self.assertTrue(response.data['new_status'][0], 'fail')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_collision_3(self):
        test_result = G(models.TestResult, name="test_name")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        modified_at = test_result.modified_at.strftime("%H:%M:%S %d-%m-%Y.%f")

        data = {'status': 'pass', 'modified_at': modified_at}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {'status': 'fail', 'modified_at': modified_at}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_collision_4(self):
        test_result = G(models.TestResult, name="test_name")
        url = '/api/test-result/%s/%s/' % (test_result.test_job.id, test_result.name)

        data = {'status': 'pass'}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {'status': 'fail'}
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
