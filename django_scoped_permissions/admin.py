from django.contrib import admin

from django_scoped_permissions.models import ScopedPermission, ScopedPermissionGroup


@admin.register(ScopedPermission)
class ScopedPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "exact",
        "exclude",
    )


@admin.register(ScopedPermissionGroup)
class ScopedPermissionGroupAdmin(admin.ModelAdmin):
    list_display = ("name",)

    filter_horizontal = ("scoped_permissions",)
