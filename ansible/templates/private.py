from . import *

AUTH_CROWD_ALWAYS_UPDATE_USER = False
AUTH_CROWD_ALWAYS_UPDATE_GROUPS = True
AUTH_CROWD_CREATE_GROUPS = True
AUTH_CROWD_APPLICATION_USER = '{{crowd_user}}'
AUTH_CROWD_APPLICATION_PASSWORD = '{{crowd_pass}}'
AUTH_CROWD_SERVER_REST_URI = '{{crowd_rest_uri}}'

AUTHENTICATION_BACKENDS = (
    'crowdrest.backend.CrowdRestBackend',
    'django.contrib.auth.backends.ModelBackend',
)

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

# LOGGING['handlers']['mail_admins'] = {
#     'include_html': True,
#     'level': 'ERROR',
#     'class': 'django.utils.log.AdminEmailHandler'
# }

# LOGGING['handlers']['file'] = {
#     'level': 'DEBUG',
#     'class': 'logging.handlers.TimedRotatingFileHandler',
#     'filename': '{{logs_base}}/django.log',
#     'backupCount': 5,
#     'when': 'midnight',
#     'encoding': 'utf8',
#     'formatter': 'verbose',
# }
