from rest_framework import mixins
from rest_framework import filters
from rest_framework import viewsets
from rest_framework import response
from rest_framework import generics
from rest_framework import permissions

from django.contrib import auth

from . import models
from . import serializers
from . import miner


class User(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = (permissions.IsAuthenticated, )
    queryset = auth.models.User.objects.all()
    serializer_class = serializers.User

    def list(self, request):
        return response.Response(self.serializer_class(self.request.user).data)


class Definition(viewsets.ModelViewSet):
    queryset = models.Definition.objects.filter(kind=models.Definition.MANUAL)
    serializer_class = serializers.Definition

    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)


class TestExecution(viewsets.ReadOnlyModelViewSet):
    queryset = models.TestExecution.objects.prefetch_related("test_jobs")
    serializer_class = serializers.TestExecution
    filter_backends = (filters.SearchFilter,)
    search_fields = ("board", "build_id", "tree", "branch", "kernel", "defconfig", "arch")


class TestJob(viewsets.ModelViewSet):
    queryset = (models.TestJob.objects
                .select_related('test_execution', 'run_definition', 'run_definition__definition')
                .prefetch_related('tests_results'))
    serializer_class = serializers.TestJob
    filter_backends = (filters.SearchFilter, filters.DjangoFilterBackend)
    search_fields = ('id', 'status', 'kind', 'test_execution__build_id', 'test_execution__board')
    filter_fields = ('test_execution',)

    def get_serializer_class(self):
        if self.request.method in ['POST', 'PUT']:
            return serializers.TestJob
        return serializers.TestJobRead

    def get_queryset(self):
        return models.Permission.ACL(self.request.user, self.queryset)


class TestResult(viewsets.ModelViewSet):
    queryset = models.TestResult.objects.select_related('test_job')
    lookup_field = ('test_job', 'name')
    lookup_value_regex = ('[^/.]+', '.+')
    serializer_class = serializers.TestResult

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        obj = generics.get_object_or_404(queryset, test_job__id=self.kwargs['test_job'],
                                         name=self.kwargs['name'])

        return obj


class TestManual(viewsets.ViewSet):

    def list(self, request):
        sha = miner.manual.sha()
        tests = miner.manual.tests()
        return response.Response({"sha": sha, "tests": tests})
