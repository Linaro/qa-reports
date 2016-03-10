from django.db import models
from django.utils import timezone

from django.db.models import Q
from django.conf import settings
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ValidationError, FieldError

from .miner import miner


class TestExecution(models.Model):
    build_id = models.CharField(max_length=24)
    board = models.CharField(max_length=256, null=True)

    tree = models.CharField(max_length=256)
    branch = models.CharField(max_length=256)
    kernel = models.CharField(max_length=256)
    defconfig = models.CharField(max_length=256)
    arch = models.CharField(max_length=256)

    created_at = models.DateTimeField(default=timezone.now)

    executable = models.BooleanField(default=False)
    submited = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        unique_together = ('build_id', 'board')

    def _is_executable(self):
        # fixme: right now we are testing only this "board"
        # this will change in future

        return self.board == "am335x-boneblack"

    def save(self, *args, **kwargs):
        self.executable = self._is_executable()
        return super(TestExecution, self).save(*args, **kwargs)

    def __str__(self):
        return "%s / %s / %s" % (self.build_id, self.board, self.created_at)


class Definition(models.Model):
    name = models.CharField(max_length=256)
    data = JSONField()

    MANUAL = 'manual'
    AUTOMATIC = 'automatic'
    KERNELCI = 'kernelci'
    KIND_CHOICES = (
        (MANUAL, 'manual'),
        (AUTOMATIC, 'automatic'),
        (KERNELCI, 'kernelci')
    )

    kind = models.CharField(max_length=256, choices=KIND_CHOICES)
    created_at = models.DateTimeField(default=timezone.now)

    def create_job(self, test_execution):
        return TestJob.objects.create(
            definition=self,
            test_execution=test_execution
        )

    class Meta:
        ordering = ['-created_at']


class RunDefinition(models.Model):
    definition = models.ForeignKey(
        'Definition',
        related_name="run_definitions",
        on_delete=models.CASCADE)

    data = JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']


class TestJobManager(models.Manager):
    def create(self, *args, **kwargs):
        # a bit messy hack,
        # we need to have a definition for miner before items is saved
        definition = kwargs.pop('definition')
        if not definition:
            return super(TestJobManager, self).create(*args, **kwargs)

        item = self.model(**kwargs)
        run_definition = RunDefinition(definition=definition)
        item.run_definition = run_definition
        item.kind = run_definition.definition.kind
        run_definition.data = miner(item).freeze()
        run_definition.save()
        item.run_definition_id = run_definition.id
        item.save()
        return item


class TestJob(models.Model):

    objects = TestJobManager()

    id = models.CharField(primary_key=True,
                          blank=False, max_length=128)

    test_execution = models.ForeignKey(
        'TestExecution',
        related_name="test_jobs",
        on_delete=models.CASCADE)

    run_definition = models.OneToOneField(
        'RunDefinition',
        null=True,
        on_delete=models.CASCADE)

    kind = models.CharField(max_length=256, editable=False)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=128, null=True)
    completed = models.BooleanField(default=False)

    private = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    @property
    def regression(self):
        return self.tests_results.filter(regression=True).count() > 0

    def save(self, *args, **kwargs):
        new = not self.id or kwargs.get('force_insert', False)
        if not self.id and new:
            self.id = miner(self).id()
        super(TestJob, self).save(*args, **kwargs)
        if new:
            miner(self).create_results()

    def __str__(self):
        return "%s / %s / %s" % (self.id, self.status, self.created_at)


class TestResult(models.Model):
    test_job = models.ForeignKey('TestJob',
                                 related_name="tests_results",
                                 on_delete=models.CASCADE)
    name = models.CharField(max_length=256)
    status = models.CharField(max_length=128, null=True)
    data = JSONField(null=True)
    regression = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)

    class Meta:
        ordering = ['-created_at']

    def previous_result(self):
        return (TestResult.objects
                .exclude(id=self.id)
                .filter(test_job__test_execution=self.test_job.test_execution,
                        created_at__lt=self.created_at)).first()

    def next_result(self):
        return (TestResult.objects
                .exclude(id=self.id)
                .filter(test_job__test_execution=self.test_job.test_execution,
                        created_at__gt=self.created_at)).last()

    def save(self, *args, **kwargs):
        previous_result = self.previous_result()
        self.regression = (previous_result is not None and
                           previous_result.status == 'pass' and
                           self.status == 'fail')
        super(TestResult, self).save(*args, **kwargs)
        next_result = self.next_result()
        if next_result:
            next_result.regression = (self.status == 'pass' and
                                      next_result.status == 'fail')
            next_result.save(update_fields=['regression'])


def validate_field(value):
    try:
        TestJob.objects.filter(**{value + '__isnull': True})
    except FieldError:
        raise ValidationError('%(value)s is not an correct field name', params={'value': value})


class Permission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name="permissions",
                             on_delete=models.CASCADE)
    field = models.CharField(max_length=256, validators=[validate_field])
    value = models.CharField(max_length=256)

    @staticmethod
    def ACL(user, queryset):
        if user.is_superuser:
            return queryset
        if user.is_anonymous():
            return queryset.filter(private=False)
        conditions = [{k: v} for k, v in user.permissions.values_list('field', 'value')]
        items = [Q(**p) for p in conditions]
        if not items:
            return queryset.filter(private=False)
        return queryset.filter(Q(private=False) | reduce(lambda x, y: x | y, items))
