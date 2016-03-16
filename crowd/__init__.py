from django.conf import settings
from django.core import exceptions

AUTH_CROWD_SERVER_REST_URI = getattr(settings, 'AUTH_CROWD_SERVER_REST_URI', None)
AUTH_CROWD_APPLICATION_USER = getattr(settings, 'AUTH_CROWD_APPLICATION_USER', None)
AUTH_CROWD_APPLICATION_PASSWORD = getattr(settings, 'AUTH_CROWD_APPLICATION_PASSWORD', None)

if not AUTH_CROWD_SERVER_REST_URI:
    raise exceptions.ImproperlyConfigured(
        'django-crowd-auth: AUTH_CROWD_SERVER_REST_URI missing in settings')

if not AUTH_CROWD_APPLICATION_USER:
    raise exceptions.ImproperlyConfigured(
        'django-crowd-auth: AUTH_CROWD_APPLICATION_USER missing in settings')

if not AUTH_CROWD_APPLICATION_PASSWORD:
    raise exceptions.ImproperlyConfigured(
        'django-crowd-auth: AUTH_CROWD_APPLICATION_PASSWORD missing in settings')

if not AUTH_CROWD_SERVER_REST_URI.endswith('/'):
    AUTH_CROWD_SERVER_REST_URI = "%s/" % AUTH_CROWD_SERVER_REST_URI

AUTH_CROWD_ALWAYS_UPDATE_USER = getattr(settings, 'AUTH_CROWD_ALWAYS_UPDATE_USER', False)
AUTH_CROWD_ALWAYS_UPDATE_GROUPS = getattr(settings, 'AUTH_CROWD_ALWAYS_UPDATE_GROUPS', True)
AUTH_CROWD_CREATE_GROUPS = getattr(settings, 'AUTH_CROWD_CREATE_GROUPS', False)

AUTH_CROWD_GROUP_MAP = getattr(settings, 'AUTH_CROWD_GROUP_MAP', {})
AUTH_CROWD_SUPERUSER_GROUP = getattr(settings, 'AUTH_CROWD_SUPERUSER_GROUP', None)
AUTH_CROWD_STAFF_GROUP = getattr(settings, 'AUTH_CROWD_STAFF_GROUP', None)
