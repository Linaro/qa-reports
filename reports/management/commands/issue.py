import os
import subprocess

from django.core.management.base import BaseCommand
from django.conf import settings

from reports import issues


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('kind')
        parser.add_argument('id')

    def handle(self, *args, **options):
        print issues.register_issues()[options['kind']](options['id'])()
