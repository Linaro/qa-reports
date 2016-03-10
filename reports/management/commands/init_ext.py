import os
import subprocess

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):

    def handle(self, *args, **options):

        for repo in settings.EXT_REPOSITORY.values():
            if os.path.exists(repo['location']):
                continue
            output = subprocess.check_output(["git", "clone", repo['git'], repo['location']],
                                             stderr=subprocess.STDOUT)

            self.stdout.write("%s %s" % (repo['git'], output.strip("\n").lower()))
