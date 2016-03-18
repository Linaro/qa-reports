from django.conf import settings
from django.contrib import admin
from django.shortcuts import render
from django.conf.urls import url, include
from django.conf.urls.static import static

from rest_framework import routers
from rest_framework.authtoken import views as authtoken

from . import views


class CustomRouter(routers.SimpleRouter):
    def get_lookup_regex(self, viewset, lookup_prefix=''):
        lookup_field = getattr(viewset, 'lookup_field', 'pk')
        lookup_url_kwarg = getattr(viewset, 'lookup_url_kwarg', None) or lookup_field

        if not isinstance(lookup_url_kwarg, (tuple, list)):
            return super(CustomRouter, self).get_lookup_regex(viewset, lookup_prefix='')

        lookup_value_regex = getattr(viewset, 'lookup_value_regex', '[^/.]+')
        base_regex = '(?P<{lookup_prefix}{lookup_url_kwarg}>{lookup_value})'

        regex = []
        for lookup_kwarg, lookup_regex in zip(lookup_url_kwarg, lookup_value_regex):
            regex.append(base_regex.format(
                lookup_prefix=lookup_prefix,
                lookup_url_kwarg=lookup_kwarg,
                lookup_value=lookup_regex
            ))
        return "/".join(regex)


router = CustomRouter()
router.register(r'user', views.User)
router.register(r'definition', views.Definition)
router.register(r'test-execution', views.TestExecution)
router.register(r'test-job', views.TestJob)
router.register(r'test-result', views.TestResult)
router.register(r'issue', views.Issue)
router.register(r'test-manual', views.TestManual, base_name="testmanual")


urlpatterns = [
    url(r'^$', lambda x: render(x, 'index.html')),
    url(r'^api/', include(router.urls)),
    url(r'^api/login/', authtoken.obtain_auth_token),
    url(r'^admin/', admin.site.urls),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
