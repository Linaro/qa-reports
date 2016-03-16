from . import *

AUTH_CROWD_ALWAYS_UPDATE_USER = False
AUTH_CROWD_ALWAYS_UPDATE_GROUPS = True
AUTH_CROWD_CREATE_GROUPS = True
AUTH_CROWD_APPLICATION_USER = '{{crowd_user}}'
AUTH_CROWD_APPLICATION_PASSWORD = '{{crowd_pass}}'
AUTH_CROWD_SERVER_REST_URI = '{{crowd_rest_uri}}'


KERNELCI_TOKEN = "{{ kernelci_token }}"
SECRET_KEY = "{{ secret_key }}"

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '{{db_name}}',
        'USER': '{{db_user}}',
        'PASSWORD': '{{db_password}}',
        'HOST': '{{db_host}}',
    }
}

INSTALLED_APPS += (
    'crowd',
)

AUTHENTICATION_BACKENDS = (
    'reports.auth.Backend',
    'django.contrib.auth.backends.ModelBackend',
)

CREDENTIALS = {
    "{{ testjob_host }}": (
        "{{ testjob_user }}",
        "{{ testjob_pass }}"
    ),
}

ALLOWED_HOSTS = ['{{ inventory_hostname }}', 'localhost']

ADMINS = [
    ("Milosz Wasilewski", 'milosz.wasilewski@linaro.org'),
    ("Sebastian Pawlus", 'sebastian.pawlus@linaro.org')
]

STATIC_ROOT = "{{ static_base }}"

EXT_REPOSITORY = {
    "manual-test-definitions": {
        "location": "{{ ext_base }}/manual-test-definitions",
        "git": "https://git.linaro.org/qa/manual-test-definitions.git"
    }
}
