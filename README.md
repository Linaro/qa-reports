# qa-reports
[![Build Status](https://travis-ci.org/Linaro/qa-reports.svg?branch=master)](https://travis-ci.org/Linaro/qa-reports)



## setup (ubuntu)

1) required system packages
    - python-dev
    - python-psycopg2
    - python-pip (or [get-pip.py](https://pip.pypa.io/en/stable/installing/#installing-with-get-pip-py))
    - libffi-dev
    - libssl-dev
    - git
    - postgresql
    - postgresql-contrib
    - libpq-dev

1) required python packages

	`pip install -U pip virtualenv`

1) project packages

	- `pip install -U pip virtualenv`
	- `virtualenv .virtualenv/`
	- `source .virtualenv/bin/activate`
	- `(.virtualenv) pip install -r requirements.txt`



## configure

1) create `settings/private.py`, append with the content, modify to the needs
	```
	from . import *

	KERNELCI_TOKEN = "FAKE-TOKEN"
	SECRET_KEY = "FAKE-TOKEN"

	QUERY_INSPECT_ENABLED = True
	QUERY_INSPECT_LOG_QUERIES = True

	MIDDLEWARE_CLASSES += (
		'qinspect.middleware.QueryInspectMiddleware',
	)

	DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			'NAME': 'qa-reports',
			'USER': 'qa-reports',
			'PASSWORD': 'qa-reports',
			'HOST': 'localhost',
		}
	}

	LOGGING['loggers']['qinspect'] = {
		'handlers': ['console'],
		'level': 'DEBUG',
		'propagate': True,
	}

	CELERY_ALWAYS_EAGER = True
	CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

	STATIC_ROOT = '/tmp/qa-reports/static'
	```

2) configure database

	- `/etc/postgresql/9.X/main/postgresql.conf` uncomment line `listen_addresses = 'localhost'`
	- `sudo -u postgres bash`
	- `createuser qa-reports`
	- `createdb qa-reports`
	- `python manage.py migrate`

3) setup external repos (ext)

	`python manage.py init_ext`



### tests

	`python manage.py test`
