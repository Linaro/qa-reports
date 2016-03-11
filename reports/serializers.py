from rest_framework import serializers

from django.contrib import auth

from . import models


class User(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'username', 'email', 'last_login')
        model = auth.models.User


class TestExecution(serializers.ModelSerializer):
    class TestJob(serializers.ModelSerializer):
        class Meta:
            model = models.TestJob

    test_jobs = TestJob(many=True, read_only=True)

    class Meta:
        model = models.TestExecution
        read_only_fields = ('id', 'created_at')


class Definition(serializers.ModelSerializer):

    class Meta:
        model = models.Definition
        read_only_fields = ('id', 'created_at')


class RunDefinition(serializers.ModelSerializer):
    definition = Definition()

    class Meta:
        model = models.RunDefinition
        read_only_fields = ('id', 'created_at')


class TestResult(serializers.ModelSerializer):
    datetime_format = "%H:%M:%S %d-%m-%Y.%f"
    modified_by = User(required=False)
    modified_at = serializers.DateTimeField(
        required=False,
        format=datetime_format,
        input_formats=[datetime_format])

    class Meta:
        model = models.TestResult
        read_only_fields = ('test_job', 'name', 'created_at', 'modified_by')

    def to_representation(self, obj):
        data = super(TestResult, self).to_representation(obj)
        if not obj.test_job.run_definition:
            return data
        if 'tests' not in obj.test_job.run_definition.data:
            return data

        data.update(obj.test_job.run_definition.data['tests'][obj.name])
        return data

    def validate(self, data):
        data['modified_by'] = self.context['request'].user

        modified_at = data.pop('modified_at', None)
        if not modified_at:
            return data

        old_timestamp = self.instance.modified_at.strftime(self.datetime_format)
        new_timestamp = modified_at.strftime(self.datetime_format)

        if old_timestamp == new_timestamp:
            return data

        if self.instance.status == data['status']:
            return data

        raise serializers.ValidationError({
            'status': self.instance.status,
            'user': User(self.context['request'].user).data
        })


class TestJob(serializers.ModelSerializer):
    definition = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=models.Definition.objects.all())

    class Meta:
        model = models.TestJob
        read_only_fields = ('id', 'run_definition', 'created_at')


class TestJobRead(TestJob):

    class TestExecution(serializers.ModelSerializer):
        class Meta:
            model = models.TestExecution

    test_execution = TestExecution()
    run_definition = RunDefinition()
    regression = serializers.BooleanField()
    results = TestResult(many=True, source="tests_results")
