from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import AbstractUser

from django_scoped_permissions.core.scoped_permission import ScopedPermission
from django_scoped_permissions.models import ScopedPermissionProvider, ProtectedModelMixin


class ScopedAuthenticationBackend(ModelBackend):
    def has_perm(self, user_obj: AbstractUser, perm, obj=None):
        if user_obj.is_anonymous:
            return False

        if user_obj.is_superuser:
            return True

        if not isinstance(user_obj, ScopedPermissionProvider):
            return None

        granting_permissions = user_obj.get_granting_permissions()

        if obj is None:
            required_permission = ScopedPermission.safe_create(perm, default=None)

            if not required_permission:
                return None

            return required_permission.check_access(granting_permissions)

        elif isinstance(obj, ProtectedModelMixin):
            return obj.check_access(granting_permissions)

        return None
