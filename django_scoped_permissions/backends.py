from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractUser

from django_scoped_permissions.models import ScopedPermissionProvider, ProtectedModelMixin


class ScopedAuthenticationBackend(ModelBackend):
    def has_perm(self, user_obj: AbstractUser, perm: str, obj=None):
        if user_obj.is_anonymous:
            return False

        if user_obj.is_superuser:
            return True

        if not isinstance(user_obj, ScopedPermissionProvider):
            return None

        if not obj:
            return user_obj.has_scoped_permissions(perm)
        elif isinstance(obj, ProtectedModelMixin):
            return obj.has_permission(user_obj, perm)
        else:
            return None
