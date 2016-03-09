from mock import patch

from django_dynamic_fixture import G
from django.test import TestCase

from reports import models


class TestDefinition(TestCase):

    def test_create_manual(self):
        mock_test = {
            'some_test_1.yaml': {'steps': [], 'expected': []},
            'some_test_2.yaml': {'steps': [], 'expected': []}
        }

        data = {"tests": ["some_test_1.yaml", "some_test_2.yaml"]}

        definition = G(models.Definition, kind=models.Definition.MANUAL, data=data)
        test_execution = G(models.TestExecution)

        with patch('reports.miner.manual.tests') as miner_tests:
            miner_tests.return_value = mock_test
            definition.create_job(test_execution)

        self.assertEqual(models.TestJob.objects.count(), 1)
        self.assertEqual(models.RunDefinition.objects.count(), 1)
        self.assertEqual(models.TestResult.objects.count(), 2)


class TestJob(TestCase):

    def test_regression_1(self):
        test_job_1 = G(models.TestJob)
        test_job_2 = G(models.TestJob)

        self.assertEqual(test_job_1.regression, False)
        self.assertEqual(test_job_2.regression, False)

    def test_regression_2(self):
        test_execution = G(models.TestExecution)
        test_job_1 = G(models.TestJob, test_execution=test_execution)
        test_job_2 = G(models.TestJob, test_execution=test_execution)

        G(models.TestResult, test_job=test_job_1, status='pass', name="test 1")
        G(models.TestResult, test_job=test_job_1, status='pass', name="test 2")
        G(models.TestResult, test_job=test_job_1, status='pass', name="test 3")

        G(models.TestResult, test_job=test_job_2, status='pass', name="test 1")
        G(models.TestResult, test_job=test_job_2, status='pass', name="test 2")
        G(models.TestResult, test_job=test_job_2, status='fail', name="test 3")

        self.assertEqual(test_job_1.regression, False)
        self.assertEqual(test_job_2.regression, True)

    def test_regression_3(self):
        test_execution = G(models.TestExecution)
        test_job_1 = G(models.TestJob, test_execution=test_execution)
        test_job_2 = G(models.TestJob, test_execution=test_execution)

        G(models.TestResult, test_job=test_job_2, status='fail', name="test 1")
        G(models.TestResult, test_job=test_job_2, status='skip', name="test 2")
        G(models.TestResult, test_job=test_job_2, status='pass', name="test 3")

        self.assertEqual(test_job_1.regression, False)
        self.assertEqual(test_job_2.regression, False)


class TestResult(TestCase):

    def test_previous(self):
        test_execution = G(models.TestExecution)

        test_job_1 = G(models.TestJob, test_execution=test_execution)
        test_job_2 = G(models.TestJob, test_execution=test_execution)
        test_job_3 = G(models.TestJob, test_execution=test_execution)

        test_result_1 = G(models.TestResult,
                          test_job=test_job_1,
                          status='pass',
                          name="test 1")

        test_result_2 = G(models.TestResult,
                          test_job=test_job_2,
                          status='fail',
                          name="test 1")

        test_result_3 = G(models.TestResult,
                          test_job=test_job_3,
                          status='fail',
                          name="test 1")

        self.assertEqual(test_result_1.previous_result(), None)
        self.assertEqual(test_result_2.previous_result(), test_result_1)
        self.assertEqual(test_result_3.previous_result(), test_result_2)

    def test_next(self):
        test_execution = G(models.TestExecution)

        test_job_1 = G(models.TestJob, test_execution=test_execution)
        test_job_2 = G(models.TestJob, test_execution=test_execution)
        test_job_3 = G(models.TestJob, test_execution=test_execution)

        test_result_1 = G(models.TestResult,
                          test_job=test_job_1,
                          status='pass',
                          name="test 1")

        test_result_2 = G(models.TestResult,
                          test_job=test_job_2,
                          status='fail',
                          name="test 1")

        test_result_3 = G(models.TestResult,
                          test_job=test_job_3,
                          status='fail',
                          name="test 1")

        self.assertEqual(test_result_1.next_result(), test_result_2)
        self.assertEqual(test_result_2.next_result(), test_result_3)
        self.assertEqual(test_result_3.next_result(), None)

    def test_regresion_1(self):
        test_execution = G(models.TestExecution)

        test_job_1 = G(models.TestJob, test_execution=test_execution)
        test_job_2 = G(models.TestJob, test_execution=test_execution)

        test_result_1 = G(models.TestResult,
                          test_job=test_job_1,
                          status='pass',
                          name="test 1")

        test_result_2 = G(models.TestResult,
                          test_job=test_job_2,
                          status='fail',
                          name="test 1")

        self.assertEqual(test_result_1.regression, False)
        self.assertEqual(test_result_2.regression, True)

    def test_regresion_2(self):
        test_execution = G(models.TestExecution)

        test_job_1 = G(models.TestJob, test_execution=test_execution)
        test_job_2 = G(models.TestJob, test_execution=test_execution)

        test_result_2 = G(models.TestResult,
                          test_job=test_job_2,
                          status='fail',
                          name="test 1")

        self.assertEqual(test_result_2.regression, False)

    def test_regresion_3(self):
        test_execution = G(models.TestExecution)

        test_job_1 = G(models.TestJob, test_execution=test_execution)
        test_job_2 = G(models.TestJob, test_execution=test_execution)
        test_job_3 = G(models.TestJob, test_execution=test_execution)

        test_result_1 = G(models.TestResult,
                          test_job=test_job_1,
                          status='pass',
                          name="test 1")

        test_result_2 = G(models.TestResult,
                          test_job=test_job_2,
                          status='fail',
                          name="test 1")

        test_result_3 = G(models.TestResult,
                          test_job=test_job_3,
                          status='fail',
                          name="test 1")

        self.assertEqual(test_result_1.regression, False)
        self.assertEqual(test_result_2.regression, True)
        self.assertEqual(test_result_3.regression, False)

    def test_regresion_4(self):
        test_execution = G(models.TestExecution)

        test_job_1 = G(models.TestJob, test_execution=test_execution)
        test_job_2 = G(models.TestJob, test_execution=test_execution)
        test_job_3 = G(models.TestJob, test_execution=test_execution, notes="xxx")

        test_result_1 = G(models.TestResult,
                          test_job=test_job_1,
                          status='pass',
                          name="test 1")

        test_result_2 = G(models.TestResult,
                          test_job=test_job_2,
                          status='fail',
                          name="test 1")

        test_result_3 = G(models.TestResult,
                          test_job=test_job_3,
                          status='fail',
                          name="test 1")

        self.assertEqual(test_result_1.regression, False)
        self.assertEqual(test_result_2.regression, True)
        self.assertEqual(test_result_3.regression, False)

        test_result_2.status = 'pass'
        test_result_2.save()

        test_result_1.refresh_from_db()
        test_result_2.refresh_from_db()
        test_result_3.refresh_from_db()

        self.assertEqual(test_result_1.regression, False)
        self.assertEqual(test_result_2.regression, False)
        self.assertEqual(test_result_3.regression, True)
