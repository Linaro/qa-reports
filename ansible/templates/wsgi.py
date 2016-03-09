import os
import sys

activate_env = os.path.expanduser("/srv/{{inventory_hostname}}/.virtualenv/bin/activate_this.py")
execfile(activate_env, dict(__file__=activate_env))

sys.path.append('/srv/{{inventory_hostname}}/project')

# import djcelery
# djcelery.setup_loader()

from django.core.wsgi import get_wsgi_application

os.environ['DJANGO_SETTINGS_MODULE'] = "reports.settings.private"
application = get_wsgi_application()
