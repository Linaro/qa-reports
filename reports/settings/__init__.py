import os

from celery.schedules import crontab
import djcelery; djcelery.setup_loader()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEBUG = True

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'rest_framework',
    'rest_framework.authtoken',
    "compressor",
    'djcelery',

    'reports',
    'reports.ui',
]


MIDDLEWARE_CLASSES = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'reports.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'ui')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_PRECOMPILERS = (
    ('text/sass', 'sassc {infile} {outfile}'),
)

WSGI_APPLICATION = 'reports.wsgi.application'

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'


REST_FRAMEWORK = {
    'DATETIME_FORMAT': "%H:%M:%S %d-%m-%Y",
    'DATETIME_INPUT_FORMATS': ["%H:%M:%S", "%H:%M:%S %d-%m-%Y"],
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'DEFAULT_PAGINATION_CLASS': 'reports.pagination.Pagination',
    'PAGE_SIZE': 30,
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.TokenAuthentication',
    )
}

KERNELCI_TOKEN = None

CELERY_ACCEPT_CONTENT = ['json', 'pickle']
BROKER_URL = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'djcelery.backends.database:DatabaseBackend'
CELERY_TIMEZONE = 'UTC'
CELERYD_HIJACK_ROOT_LOGGER = False

CELERYD_LOG_FORMAT = '[%(asctime)s] %(levelname)s: %(message)s'
CELERYD_TASK_LOG_FORMAT = '[%(asctime)s] %(levelname)s %(task_name)s: %(message)s'

CELERYBEAT_SCHEDULE = {
    'Pull kernelCI': {
        'task': 'reports.tasks.kernelci_pull',
        'schedule': crontab(minute='*/20')
    },

    'Deploy TestJobs': {
        'task': 'reports.tasks.testjob_submit',
        'schedule': crontab(minute='*/5')
    },
    'Check TestJobs': {
        'task': 'reports.tasks.testjob_check',
        'schedule': crontab(minute='*/5')
    },
    'Check TestJobs from KernelCI': {
        'task': 'reports.tasks.testjob_kernelci_check',
        'schedule': crontab(minute='*/10')
    },
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'simple': {
            'format': u'[%(asctime)s] %(levelname)-8s %(message)s',
        }
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'tasks': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        }
    }
}

EXT_REPOSITORY = {
    "manual-test-definitions": {
        "location": os.path.join(os.path.dirname(BASE_DIR), 'ext', "manual-test-definitions"),
        "git": "https://git.linaro.org/qa/manual-test-definitions.git"
    }
}

CREDENTIALS = {
    'validation.linaro.org': ('user', "password"),
}

DDF_FIELD_FIXTURES = {
    'django.contrib.postgres.fields.jsonb.JSONField': {
        'ddf_fixture': lambda: []
    },
}
