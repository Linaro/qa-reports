from . import *

SECRET_KEY = 'travis'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'qa-reports',
        'USER': 'qa-reports',
        'PASSWORD': 'qa-reports',
        'HOST': 'localhost',
    }
}

STATIC_ROOT = '/tmp/qa-reports/static'
