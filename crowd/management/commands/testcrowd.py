from django.core.management.base import BaseCommand
from crowd.backend import CrowdBackend


class Command(BaseCommand):

    help = ("Try to authenticate a user via Crowd "
            "(testing crowed backend with current settings)")

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('password')

    def handle(self, *args, **options):

        user = CrowdBackend().authenticate(options['username'], options['password'])
        if not user:
            self.stdout.write(self.style.ERROR("Username and password are incorrect"))
            return

        if user.is_active:
            msg = self.style.SUCCESS("You provided a correct username and password")
        else:
            msg = self.style.WARNING("Account has been disabled")

        self.stdout.write(msg)
