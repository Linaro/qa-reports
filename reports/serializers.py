from rest_framework import serializers

from django.contrib import auth

from . import models
from .miner import miner


class User(serializers.ModelSerializer):

    class Meta:
        fields = ('id', 'username', 'email', 'last_login')
        model = auth.models.User


class TestJobExecution(serializers.ModelSerializer):

    class Meta:
        model = models.TestJob


class TestExecution(serializers.ModelSerializer):
    test_jobs = TestJobExecution(many=True, read_only=True)

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
    modifed_at = serializers.DateTimeField(required=False)

    class Meta:
        model = models.TestResult
        read_only_fields = ('created_at',)


class TestJob(serializers.ModelSerializer):
    definition = serializers.PrimaryKeyRelatedField(
        write_only=True,
        queryset=models.Definition.objects.all())

    class Meta:
        model = models.TestJob
        read_only_fields = ('id', 'run_definition', 'created_at')


class TestJobExecution(serializers.ModelSerializer):
    class Meta:
        model = models.TestExecution


class TestJobRead(TestJob):
    test_execution = TestJobExecution()
    run_definition = RunDefinition()
    results = serializers.SerializerMethodField()
    regression = serializers.BooleanField()

    def get_results(self, obj):
        return miner(obj).get_results()


class TestResultUpdate(serializers.ModelSerializer):
    datetime_format = "%H:%M:%S %d-%m-%Y.%f"
    modifed_at = serializers.DateTimeField(required=False,
                                           format=datetime_format,
                                           input_formats=[datetime_format])

    class Meta:
        model = models.TestResult
        fields = ('status', 'modifed_at')
        read_only_fields = ('created_at',)

    def validate(self, data):
        modifed_at = data.pop('modifed_at', None)

        if not modifed_at:
            return data

        old_timestamp = self.instance.modifed_at.strftime(self.datetime_format)
        new_timestamp = modifed_at.strftime(self.datetime_format)

        if old_timestamp == new_timestamp:
            return data

        if self.instance.status == data['status']:
            return data

        raise serializers.ValidationError({
            'status': self.instance.status
        })
