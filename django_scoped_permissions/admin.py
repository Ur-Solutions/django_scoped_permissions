from django.contrib import admin

from django_scoped_permissions.models import StoredScopedPermission


@admin.register(StoredScopedPermission)
class StoredScopedPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "scope",
        "verb",
        "is_exact",
        "is_negation",
    )
