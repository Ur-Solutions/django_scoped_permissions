from functools import reduce
from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from django_scoped_permissions.core.scoped_permission import ScopedPermissionLike, ScopedPermission


def overload_scoped_permission_like(value: "ScopedPermissionLike") -> "ScopedPermission":
    from django_scoped_permissions.core.scoped_permission import ScopedPermission
    if isinstance(value, ScopedPermission):
        return value
    else:
        return ScopedPermission.create(value)


def check_scoped_permission(
        required_permission: "ScopedPermissionLike" = "",
        granting_permission: "ScopedPermissionLike" = "",
        required_permissions: List["ScopedPermissionLike"] = None,
        granting_permissions: List["ScopedPermissionLike"] = None,
) -> bool:
    """
    This is a helper method which checks if a granting permission provides access to a required permission.
    """

    # Fail if both singular and plural variants are given
    if required_permission != "" and required_permissions is not None:
        raise ValueError("Only one of required_permission and required_permissions can be given")

    if granting_permission != "" and granting_permissions is not None:
        raise ValueError("Only one of granting_permission and granting_permissions can be given")

    if required_permissions is None:
        required_permissions = [required_permission]

    if granting_permissions is None:
        granting_permissions = [granting_permission]

    required_permissions = [overload_scoped_permission_like(permission) for permission in
                            required_permissions]
    granting_permissions = [overload_scoped_permission_like(permission) for permission in
                            granting_permissions]

    if len(required_permissions) == 1 and len(granting_permissions) == 1:
        return required_permissions[0].check_access(granting_permissions[0])

    return True
