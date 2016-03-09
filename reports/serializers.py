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

    class Meta:
        model = models.TestResult
        fields = ('status',)
        read_only_fields = ('created_at',)
