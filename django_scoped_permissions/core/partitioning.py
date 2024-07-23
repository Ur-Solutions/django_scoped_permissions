from typing import List, TYPE_CHECKING, TypedDict

from django_scoped_permissions.core.check_scoped_permission import overload_scoped_permission_like

if TYPE_CHECKING:
    from django_scoped_permissions.core.scoped_permission import ScopedPermissionLike


class PartitionedPermissions(TypedDict):
    exclude_exact: List["ScopedPermissionLike"]
    include_exact: List["ScopedPermissionLike"]
    exclude: List["ScopedPermissionLike"]
    include: List["ScopedPermissionLike"]


def partition_scoped_permissions(permissions: List["ScopedPermissionLike"]) -> PartitionedPermissions:
    """
    Partitions the set of permissions into four sets:
        - Exclude exact
        - Include exact
        - Exclude
        - Include
    """
    permissions = [overload_scoped_permission_like(permission) for permission in permissions]

    return {
        "exclude_exact": [permission for permission in permissions if permission.is_exact and permission.is_negation],
        "include_exact": [permission for permission in permissions if
                          permission.is_exact and not permission.is_negation],
        "exclude": [permission for permission in permissions if not permission.is_exact and permission.is_negation],
        "include": [permission for permission in permissions if not permission.is_exact and not permission.is_negation],
    }
