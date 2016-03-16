from django.conf import settings
from rest_framework import permissions


def has_access_rights(user):
    return user.groups.filter(name=settings.ACCESS_GROUP).exists()


def has_edit_rights(user):
    return user.groups.filter(name=settings.EDIT_GROUP).exists()


class Permissions(permissions.BasePermission):

    def has_permission(self, request, view):
        user = request.user

        if not user:
            return False

        if not user.is_authenticated():
            return False

        if user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS and has_access_rights(user):
            return True

        if request.method not in permissions.SAFE_METHODS and has_edit_rights(user):
            return True

        return False
