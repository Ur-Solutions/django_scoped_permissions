from django.contrib import admin

from django_scoped_permissions.models import ScopedPermission


@admin.register(ScopedPermission)
class ScopedPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "exact",
        "exclude",
    )
