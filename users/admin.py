from django.contrib import admin

from users.models import User, UserType

admin.site.register(User)
admin.site.register(UserType)
