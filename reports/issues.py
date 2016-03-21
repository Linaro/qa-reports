import requests


class BaseIssue(object):

    def __init__(self, remote_id):
        self.remote_id = remote_id


class Github(BaseIssue):
    name = 'github'
    url = "https://api.github.com/repos/Linaro/qa-reports/issues/%s"

    def __call__(self):
        response = requests.get(self.url % self.remote_id)
        return response.json()['html_url']
