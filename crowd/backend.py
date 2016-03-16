import logging
import requests

from django.contrib.auth.models import User, Group

import crowd

logger = logging.getLogger(__name__)


class CrowdBackend(object):

    AUTH = (crowd.AUTH_CROWD_APPLICATION_USER,
            crowd.AUTH_CROWD_APPLICATION_PASSWORD)

    def sync_user(self, user):
        if not crowd.AUTH_CROWD_ALWAYS_UPDATE_USER:
            return
        data = self.crowd_user(user.username)
        user.first_name = data.get('first-name', user.first_name)
        user.last_name = data.get('last-name', user.last_name)
        user.email = data.get('email', user.email)
        user.is_active = data.get('active', user.is_active)
        user.save()

    def sync_groups(self, user):
        if not crowd.AUTH_CROWD_ALWAYS_UPDATE_GROUPS:
            return
        data = self.crowd_get_groups(user.username)
        group_names = [x["name"] for x in data["groups"]]
        group_map = crowd.AUTH_CROWD_GROUP_MAP
        group_names = [group_map.get(x, x) for x in group_names]
        group_names = set(group_names)

        su_group = crowd.AUTH_CROWD_SUPERUSER_GROUP
        if su_group:
            if su_group in group_names:
                user.is_superuser = True
            else:
                user.is_superuser = False

        staff_group = crowd.AUTH_CROWD_STAFF_GROUP
        if staff_group:
            if staff_group in group_names:
                user.is_staff = True
            else:
                user.is_staff = False

        if crowd.AUTH_CROWD_CREATE_GROUPS:
            user.groups = [
                Group.objects.get_or_create(name=g)[0] for g in group_names
            ]
        else:
            user.groups = Group.objects.filter(name__in=group_names)

        user.save()

    def create_or_update_user(self, user_id):
        "Create or update django user of given identifier"
        user, created = User.objects.get_or_create(username=user_id)
        save_user = False

        if created:
            user.set_unusable_password()

        self.sync_user(user)

        if crowd.AUTH_CROWD_ALWAYS_UPDATE_GROUPS:
            self.sync_groups(user)
            save_user = True

        if save_user:
            user.save()

        return user

    def crowd_user(self, username):
        logger.debug("Fetching details of '%s'..." % username)

        url = "%suser.json?username=%s" % (
            crowd.AUTH_CROWD_SERVER_REST_URI,
            username
        )

        response = requests.get(url, auth=self.AUTH)
        if response.status_code == 200:
            return response.json()

        response.raise_for_status()

    def crowd_get_groups(self, username):

        url = "%suser/group/nested.json?username=%s" % (
            crowd.AUTH_CROWD_SERVER_REST_URI,
            username
        )

        response = requests.get(url, auth=self.AUTH)
        if response.status_code == 200:
            return response.json()

        response.raise_for_status()

    def crowd_authentication(self, username, password):

        url = "%sauthentication.json?username=%s" % (
            crowd.AUTH_CROWD_SERVER_REST_URI,
            username
        )

        response = requests.post(url, auth=self.AUTH, json={"value": password})

        if response.status_code == 200:
            return True
        if response.status_code == 401:
            logger.error(
                "Unauthorized access to application check "
                "'AUTH_CROWD_APPLICATION_USER' and "
                "AUTH_CROWD_APPLICATION_PASSWORD'")
        if response.status_code == 400:
            message = ", ".join(response.json().values())
            logger.info("Authenticate '%s' failed: %s" % (username, message))
            return False

        response.raise_for_status()

    def authenticate(self, username=None, password=None):
        logger.debug("Authenticate '%s'..." % username)

        if not self.crowd_authentication(username, password):
            return

        logger.debug("Authenticate '%s' successfully." % username)

        return self.create_or_update_user(username)

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
