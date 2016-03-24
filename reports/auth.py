from django.conf import settings
from crowd_auth.backend import CrowdBackend


class Backend(CrowdBackend):

    def authenticate(self, username=None, password=None):
        user = super(Backend, self).authenticate(username, password)
        if user and (user.is_superuser or
                     user.groups.filter(name=settings.ACCESS_GROUP).exists()):
            return user
        return None
