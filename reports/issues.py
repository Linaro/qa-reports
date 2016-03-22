import pyclbr
import requests
import urlparse

from django.conf import settings


def register_issues():
    klasses = [globals().get(a.name) for a in
               pyclbr.readmodule('reports.issues').values()]

    return {a.name: a for a in klasses if hasattr(a, 'name')}


class BaseIssue(object):
    auth = None

    def get_auth(self, url):
        if self.auth:
            return self.auth
        return settings.CREDENTIALS.get(urlparse.urlparse(self.url).netloc)

    def __init__(self, remote_id):
        self.remote_id = remote_id


class Bugzilla(BaseIssue):

    def __call__(self):
        url = "%s/rest/bug/%s" % (self.url, self.remote_id)
        auth = self.get_auth(url)

        response = requests.get(url, auth=auth)

        if response.status_code == 200:
            data = response.json()
            return (data['bugs'][0]['summary'],
                    data['bugs'][0]['status'],
                    '%s/show_bug.cgi?id=%s' % (self.url, self.remote_id))
        if response.status_code == 404:
            return None
        response.raise_for_status()


class Bugzilla96Boards(Bugzilla):
    name = '96boards'
    url = "https://bugs.96boards.org"


class BugzillaLinaro(Bugzilla):
    name = 'linaro'
    url = "https://bugs.linaro.org"


class Github(BaseIssue):
    name = 'kernelci'
    repo = 'kernelci/kernel-bugs'
    url = "https://api.github.com/repos/%s/issues"

    def __call__(self):
        url = "%s/%s" % (self.url % self.repo, self.remote_id)
        auth = self.get_auth(url)

        response = requests.get(url, auth=auth)

        if response.status_code == 200:
            data = response.json()
            return (data['title'], data['state'], data['html_url'])
        if response.status_code == 404:
            return None
        response.raise_for_status()
