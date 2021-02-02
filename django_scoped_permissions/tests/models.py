from django.contrib.auth.models import AbstractUser
from django.db import models

from django_scoped_permissions.core import create_scope
from django_scoped_permissions.models import (
    ScopedPermissionHolder,
    ScopedModelMixin,
    ScopedModel,
)


class User(AbstractUser, ScopedPermissionHolder, ScopedModel):
    class Meta:
        indexes = (models.Index(fields=("email",)),)

    email = models.EmailField(unique=True)

    has_registered = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_required_scopes(self):
        return [create_scope(User, self.id)]

    def get_granting_scopes(self):
        scopes = self.resolved_scopes

        for user_type in self.user_types.all():
            scopes.extend(user_type.get_granting_scopes())

        scopes.append(f"user:{self.id}")
        return scopes

    def get_name_or_username(self):
        return self.get_full_name() or self.username

    def clean(self):
        self.username = self.username.lower()
        self.email = self.email.lower()

    def __str__(self):
        return "User %s" % (self.username,)


class Company(models.Model):
    class Meta:
        pass

    name = models.CharField(max_length=128)
    short_name = models.CharField(max_length=32)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    users = models.ManyToManyField(User, related_name="companies")

    email = models.CharField(max_length=256, null=True, blank=True)

    def __str__(self):
        return self.name


class UserType(ScopedPermissionHolder, ScopedModelMixin, models.Model):
    class Meta:
        pass

    name = models.CharField(max_length=128)

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name="user_types"
    )
    users = models.ManyToManyField(User, blank=True, related_name="user_types")
    is_administrator = models.BooleanField(default=False)

    color = models.CharField(max_length=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_base_scopes(self):
        return [
            create_scope("usertype", self.id),
            create_scope("company", self.company.id, "usertype", self.id),
        ]

    def clean(self):
        if isinstance(self.color, str) and self.color.startswith("#"):
            self.color = self.color[1:]

    def __str__(self):
        return f"{self.name} ({self.company.name})"


class Pet(ScopedModelMixin, models.Model):
    class Meta:
        pass

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pets")

    name = models.CharField(max_length=128)
    age = models.PositiveIntegerField()

    def get_required_scopes(self):
        return [
            create_scope("pet", self.id),
            create_scope("user", self.user.id, "pet", self.id),
        ]

    def __str__(self):
        return self.name
