from django.contrib import admin

from permissions.models import ScopedPermission

admin.site.register(ScopedPermission)
