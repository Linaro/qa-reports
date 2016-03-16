from . import *

SECRET_KEY = 'travis'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'qa-reports',
        'USER': 'postgres',
        'PASSWORD': 'qa-reports',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}

STATIC_ROOT = '/tmp/qa-reports/static'

AUTH_CROWD_SERVER_REST_URI = 'http://localhost:8000'
AUTH_CROWD_APPLICATION_USER = 'demo'
AUTH_CROWD_APPLICATION_PASSWORD = 'demo'

INSTALLED_APPS += (
    'crowd',
)
