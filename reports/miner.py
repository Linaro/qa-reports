import git
import uuid
import yaml
import json

from django.conf import settings

from reports.testminer import GenericLavaTestSystem
from reports.kernelci import kernelci as kernelciapi


def miner(item):
    return globals()[item.kind](item)


class automatic(object):
    url = "http://validation.linaro.org/RPC2"
    username, password = settings.CREDENTIALS['validation.linaro.org']

    def __init__(self, test_job):
        self.test_job = test_job
        self.lava = GenericLavaTestSystem(self.url, self.username, self.password)

    def id(self):
        return self.lava.call_xmlrpc('scheduler.submit_job',
                                     json.dumps(self.test_job.run_definition.definition.data))

    def freeze(self):
        # fixme, this should be a template
        return self.test_job.run_definition.definition.data

    def create_results(self):
        terminal_status = ["Complete", "Incomplete", "Canceled"]

        status = self.lava.get_test_job_status(self.test_job.id)

        self.test_job.status = status

        if self.test_job.status in terminal_status:
            self.test_job.completed = True

        self.test_job.save()

        if status == "Complete":
            bundle = self.lava.call_xmlrpc('scheduler.job_status',
                                           self.test_job.id)['bundle_sha1']
            content = self.lava.call_xmlrpc('dashboard.get', bundle)['content']
            data = json.loads(content)
            self.test_job.tests_results.all().delete()
            for test_runs in data['test_runs']:
                for test_result in test_runs['test_results']:
                    self.test_job.tests_results.create(
                        name=test_result['test_case_id'],
                        status=test_result['result'],
                        data=test_result
                    )


class kernelci(object):

    def __init__(self, test_job):
        self.test_job = test_job

    def create_results(self):
        results = kernelciapi(
            'test/case',
            test_suite_id=self.test_job.id)['result']

        for test in results:
            self.test_job.tests_results.create(
                name=test['name'],
                status=test['status'].lower()
            )


class manual(object):

    def __init__(self, test_job):
        self.test_job = test_job

    def id(self):
        return str(uuid.uuid4()).replace('-', '')

    @classmethod
    def repo(self):
        return git.Repo(settings.EXT_REPOSITORY["manual-test-definitions"]['location'])

    @classmethod
    def sha(self):
        return self.repo().head.commit.hexsha

    @classmethod
    def tests(self):
        tests = {}

        for item in self.repo().tree().traverse():
            if item.path.endswith(".yaml"):
                data = yaml.load(item.data_stream.read())

                metadata = data['metadata']
                expected = data['run'].get('expected')
                steps = data['run'].get('steps')

                tests[item.path] = {
                    "name": item.path,
                    "steps": steps,
                    "metadata": metadata,
                    "expected": expected,
                }

        return tests

    def freeze(self):
        tests = {}
        available = self.tests()

        for test in self.test_job.run_definition.definition.data['tests']:
            tests[test] = available[test]

        return {
            "sha": self.repo().head.commit.hexsha,
            "tests": tests
        }

    def create_results(self):
        for name in self.test_job.run_definition.data['tests'].keys():
            self.test_job.tests_results.create(name=name)
