from . import *

AUTH_CROWD_ALWAYS_UPDATE_USER = False
AUTH_CROWD_ALWAYS_UPDATE_GROUPS = True
AUTH_CROWD_CREATE_GROUPS = True
AUTH_CROWD_APPLICATION_USER = '{{crowd_user}}'
AUTH_CROWD_APPLICATION_PASSWORD = '{{crowd_pass}}'
AUTH_CROWD_SERVER_REST_URI = '{{crowd_rest_uri}}'

BROKER_URL = 'amqp://guest:guest@localhost:5672/{{ inventory_hostname }}'

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
    'crowd_auth',
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
    "{{ bugs_linaro_org_host }}": (
        "{{ bugs_linaro_org_user }}",
        "{{ bugs_linaro_org_pass }}"
    ),
    "{{ bugs_96boards_org_host }}": (
        "{{ bugs_96boards_org_user }}",
        "{{ bugs_96boards_org_pass }}"
    )
}

ALLOWED_HOSTS = ['{{ inventory_hostname }}', 'localhost']

ADMINS = [
    # ("Milosz Wasilewski", 'milosz.wasilewski@linaro.org'),
    ("Sebastian Pawlus", 'sebastian.pawlus@linaro.org')
]

STATIC_ROOT = "{{ static_base }}"

EXT_REPOSITORY = {
    "manual-test-definitions": {
        "location": "{{ ext_base }}/manual-test-definitions",
        "git": "https://git.linaro.org/qa/manual-test-definitions.git"
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'mail_admins': {
            'include_html': True,
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'filename': '{{logs_base}}/django.log',
            'backupCount': 5,
            'when': 'midnight',
            'encoding': 'utf8',
            'formatter': 'verbose',

        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'tasks': {
            'handlers': ['mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'celery': {
            'handlers': ['mail_admins'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}
