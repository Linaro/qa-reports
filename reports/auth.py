from django.conf import settings
from crowd.backend import CrowdBackend


class Backend(CrowdBackend):

    def authenticate(self, username=None, password=None):
        user = super(Backend, self).authenticate(username, password)
        if user.is_superuser():
            return user
        if user and user.groups.filter(name=settings.ACCESS_GROUP).exists():
            return user
        return None
