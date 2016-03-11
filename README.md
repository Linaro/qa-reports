# qa-reports
[![Build Status](https://travis-ci.org/Linaro/qa-reports.svg?branch=master)](https://travis-ci.org/Linaro/qa-reports)


## setup (ubuntu)

1) required system packages

```
sudo apt-get install python-dev python-pip libffi-dev libssl-dev git
```

1) postgresql

```
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ trusty-pgdg main" >> /etc/apt/sources.list.d/postgresql.list'
sudo apt-get install postgresql-9.5 postgresql-contrib-9.5 libpq-dev
```

1) required python packages

```
sudo pip install -U pip virtualenv
```

1) project packages

```
git clone <repo>
cd qa-reports
virtualenv .virtualenv/
source .virtualenv/bin/activate
pip install -r requirements.txt
```


## configure

1) create `reports/settings/private.py`, append with the content, modify to the needs

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

In `/etc/postgresql/9.5/main/pg_hba.conf` change
change line `local all all md5` to `local all all trust`

```	
sudo service postgresql restart
```

```
sudo -u postgres bash
createuser qa-reports -d	
createdb -U qa-reports qa-reports
exit
```

```
python manage.py migrate
```

3) setup external repos (ext)

```
python manage.py init_ext
```


### development server
```
python manage.py runserver 0.0.0.0:8000
```



### tests
```
python manage.py test
```
