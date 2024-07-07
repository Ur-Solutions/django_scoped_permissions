from typing import Optional

from django.db import models

from django_scoped_permissions.core.old_core import any_scope_matches, scopes_grant_permissions


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


class ScopedPermissionHolderMixin:
    def get_granting_scopes(self):
        return []

    def has_scoped_permissions(self, *required_scopes):
        return self.has_any_scoped_permissions(*required_scopes)

    def has_any_scoped_permissions(self, *required_scopes):
        scopes = self.get_granting_scopes()

        return scopes_grant_permissions(required_scopes, scopes)

    def has_all_scoped_permissions(self, *required_scopes):
        scopes = self.get_granting_scopes()

        for scope in required_scopes:
            if not any_scope_matches([scope], scopes):
                return False

        return True

    def has_access_to(self, model: "ScopedModelMixin", verb: Optional[str] = None):

        granting_scopes = self.get_granting_scopes()
        required_scopes = model.get_required_scopes()

        return scopes_grant_permissions(required_scopes, granting_scopes, verb)


class ScopedPermissionHolder(models.Model, ScopedPermissionHolderMixin):
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

    def get_scopes(self):
        """
        DEPRECATED: Use `get_granting_scopes` instead
        """
        return self.resolved_scopes

    def get_granting_scopes(self):
        return self.resolved_scopes

    def has_scoped_permissions(self, *required_scopes):
        return self.has_any_scoped_permissions(*required_scopes)

    def has_any_scoped_permissions(self, *required_scopes):
        scopes = self.get_granting_scopes()

        return scopes_grant_permissions(required_scopes, scopes)

    def has_all_scoped_permissions(self, *required_scopes):
        scopes = self.get_granting_scopes()

        for scope in required_scopes:
            if not any_scope_matches([scope], scopes):
                return False

        return True

    def add_or_create_permission(
            self, scoped_permission: str, is_exact=False, is_negation=False
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


# DEPRECATED: Use ScopedPermissionHolder
HasScopedPermissionMixin = ScopedPermissionHolder


class ScopedModelMixin:
    def get_base_scopes(self):
        """
        DEPRECATED: Use `get_required_scopes`
        """
        return self.get_required_scopes()

    def get_required_scopes(self):
        return []

    def can_be_accessed_by(
            self, holder: ScopedPermissionHolderMixin, verb: Optional[str] = None
    ):
        user_scopes = holder.get_granting_scopes()
        required_scopes = self.get_required_scopes()

        return scopes_grant_permissions(required_scopes, user_scopes, verb)

    def has_permission(
            self, user: ScopedPermissionHolderMixin, verb: Optional[str] = None
    ):
        """
        DEPRECATED: Use `can_be_accessed_by`.
        """
        return self.can_be_accessed_by(user, verb)


class ScopedModel(models.Model, ScopedModelMixin):
    class Meta:
        abstract = True
