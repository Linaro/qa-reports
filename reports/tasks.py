import pytz
import logging

from datetime import datetime, timedelta

from django.utils import timezone

from reports import celery_app
from reports.kernelci import kernelci
from reports.models import TestExecution, Definition, TestJob

from reports import miner

logger = logging.getLogger("tasks")


def _get_boots(build_id):
    boots = kernelci("boots", build_id=build_id)['result']
    if all([b['status'] == 'PASS' for b in boots]):
        if boots:
            pass
        return [(a['_id']['$oid'], a['board'], a['dtb']) for a in boots]
    return []


@celery_app.task(bind=True)
def kernelci_pull(self):

    def created_on(r):
        return datetime.fromtimestamp(
            r['created_on']['$date'] / 1000, pytz.UTC)

    then = datetime.now(pytz.UTC) - timedelta(hours=5)
    results = kernelci("build", date_range=1)['result']
    results = [r for r in results if created_on(r) > then]

    for build in results:
        build_id = build['_id']['$oid']
        items = _get_boots(build_id)

        for build_id, board, dtb in items:
            try:
                test_execution = TestExecution.objects.get(
                    build_id=build_id,
                    board=board
                )
                logger.info("Execution exists %s "
                            % test_execution)
                continue
            except TestExecution.DoesNotExist:
                pass

            timestamp = datetime.fromtimestamp(build['created_on']['$date'] / 1000)
            created_at = timezone.make_aware(timestamp, pytz.UTC)

            tree = build['job']
            branch = build['git_branch']
            kernel = build['kernel']
            defconfig = build['defconfig']
            arch = build['arch']

            dir = "/var/www/images/kernel-ci/"
            storage = "https://storage.kernelci.org"

            dtb_url = "%s/%s/%s" % (storage,
                                    build['dirname'].replace(dir, ""),
                                    dtb)

            image_url = "%s/%s/%s" % (storage,
                                      build['dirname'].replace(dir, ""),
                                      build['kernel_image'])

            test_execution = TestExecution.objects.create(
                build_id=build_id,
                board=board,
                tree=tree,
                branch=branch,
                kernel=kernel,
                defconfig=defconfig,
                arch=arch,

                dtb_url=dtb_url,
                image_url=image_url,

                created_at=created_at
            )

            logger.info("Execution created %s" % test_execution)


@celery_app.task(bind=True)
def testjob_automatic_create(self):
    # dodaj template
    definition = Definition.objects.get(kind=Definition.AUTOMATIC)  # lava
    to_deploy = (TestExecution.objects
                 .filter(executable=True)
                 .exclude(test_jobs__run_definition__definition=definition))

    for test_execution in to_deploy:
        definition = Definition.objects.get(kind=Definition.AUTOMATIC)
        test_job = TestJob.objects.create(
            definition=definition,
            test_execution=test_execution
        )

        logger.info("TestJob %s, for %s deployed" % (test_job, test_execution))


@celery_app.task(bind=True)
def testjob_automatic_check(self):
    for test_job in TestJob.objects.filter(
            completed=False,
            run_definition__definition__kind=Definition.AUTOMATIC):

        miner.automatic(test_job).create_results()


@celery_app.task(bind=True)
def testjob_kernelci_check(self):
    suites = kernelci("test/suite")['result']

    for suite in suites:
        if not suite['board']:
            continue

        build_id = suite['build_id']['$oid']
        board = suite['board']

        try:
            test_execution = TestExecution.objects.get(
                build_id=build_id,
                board=board
            )
            logger.info("Execution exists %s " % test_execution)
        except TestExecution.DoesNotExist:
            build = kernelci(
                "build/" + suite['build_id']['$oid'])['result'][0]

            timestamp = datetime.fromtimestamp(
                build['created_on']['$date'] / 1000)

            created_at = timezone.make_aware(timestamp, pytz.UTC)

            tree = build['job']
            branch = build['git_branch']
            kernel = build['kernel']
            defconfig = build['defconfig']
            arch = build['arch']

            test_execution = TestExecution.objects.create(
                build_id=build_id,
                board=board,
                tree=tree,
                branch=branch,
                kernel=kernel,
                defconfig=defconfig,
                arch=arch,
                created_at=created_at
            )

        test_job, _ = TestJob.objects.get_or_create(
            id=suite['_id']['$oid'],
            test_execution=test_execution,
            kind='kernelci')

        if not test_job.tests_results.count():
            test_job.delete()
