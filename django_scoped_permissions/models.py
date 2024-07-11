from typing import List, Optional, TYPE_CHECKING

from django.db import models
from typing_extensions import deprecated

from django_scoped_permissions.core.check_scoped_permission import overload_scoped_permission_like

if TYPE_CHECKING:
    from django_scoped_permissions.core.scoped_permission import ScopedPermissionLike


class StoredScopedPermission(models.Model):
    class Meta:
        unique_together = (("scope", "verb", "is_negation", "is_exact"),)

    scope = models.TextField(blank=False)
    verb = models.TextField(blank=True, null=True)
    is_negation = models.BooleanField(
        default=False,
        help_text="Whether this should be a negation, meaning that if scope is 'user:update' and is_negation is True then users with this usertype will not be able to update users, even their own.",
    )
    is_exact = models.BooleanField(
        default=False,
        help_text="If checked, the permission needs an exact match to count. In other words, it does not work recursively as standard scoped permissions.",
    )

    def get_scope_parts(self):
        return self.scope.split(":")

    def __str__(self):
        permission = self.scope

        if self.verb:
            permission = f"{permission}@{self.verb}"

        if self.is_exact:
            permission = f"={permission}"

        if self.is_negation:
            permission = f"-{permission}"

        return permission


class ScopedPermissionProviderMixin:

    @deprecated("Use `get_granting_permissions` instead")
    def get_granting_scopes(self):
        return self.get_granting_permissions()

    def get_granting_permissions(self, context=None):
        return []


class StatelessScopedPermissionProvider(ScopedPermissionProviderMixin):
    pass


class ScopedPermissionProvider(models.Model, ScopedPermissionProviderMixin):
    class Meta:
        abstract = True

    scoped_permissions = models.ManyToManyField(StoredScopedPermission, blank=True)

    @property
    def resolved_scopes(self):
        from django_scoped_permissions.core.scoped_permission import ScopedPermission
        scopes = self.scoped_permissions.all()

        return [
            ScopedPermission.from_model(scope)
            for scope in scopes
        ]

    def get_granting_permissions(self, context=None):
        return self.resolved_scopes

    def add_or_create_permission(
            self, scoped_permission: "ScopedPermissionLike"
    ):
        from django_scoped_permissions.core.scoped_permission import sp
        """
        Helper method which adds a permission defined by the arguments to the permission holder.
        If a ScopedPermission object matching the argument does not exist, a new one will be created.

        The is_exact and is_negation properties of the scope can be added either directly in the string, e.g.

            add_or_create_permission("-=scope1:scope2")

        Or as parameters

            add_or_create_permission("scope1:scope2", is_exact=False, is_negation=False)
        """

        scoped_permission = sp(scoped_permission)

        scope, _ = StoredScopedPermission.objects.get_or_create(
            scope=scoped_permission.scope,
            verb=scoped_permission.verb,
            is_negation=scoped_permission.is_negation,
            is_exact=scoped_permission.is_exact
        )

        self.scoped_permissions.add(scope)


class ProtectedModelMixin:

    @deprecated("Use `get_required_permissions` instead")
    def get_required_scopes(self):
        return self.get_required_permissions()

    def get_required_permissions(self, context=None):
        return []

    def check_access(self, permissions: "ScopedPermissionLike" | List["ScopedPermissionLike"]):
        required_permissions = self.get_required_permissions()

        required_scopes = [overload_scoped_permission_like(permission) for permission in required_permissions]

        for required_scope in required_scopes:
            if not required_scope.check_access(permissions):
                return False

        return True


class ProtectedModel(models.Model, ProtectedModelMixin):
    class Meta:
        abstract = True


# DEPRECATED: Use ScopedPermissionProvider
ScopedPermissionHolder = ScopedPermissionProvider

# DEPRECATED: Use ProtectedModel
ScopedModel = ProtectedModel
