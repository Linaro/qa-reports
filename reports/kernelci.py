import requests

from django.conf import settings


headers = {"Authorization": settings.KERNELCI_TOKEN}

defaults = {
    "limit": 10000,
    "sort_order": -1,
    "sort": "created_on"
}

url = "https://api.kernelci.org/"


def kernelci(handler, **kwargs):

    url = "https://api.kernelci.org/%s/" % handler

    params = defaults.copy()
    params.update(kwargs)

    response = requests.get(
        url,
        headers=headers,
        params=params
    )
    return response.json()
