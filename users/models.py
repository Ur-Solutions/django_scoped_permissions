from django.db import models
from django.contrib.auth.models import AbstractUser, Permission

from permissions.models import HasScopedPermissionsMixin, ScopedModelMixin
from permissions.util import create_scope


class User(HasScopedPermissionsMixin, AbstractUser):
    class Meta:
        indexes = (models.Index(fields=("email",)),)

    email = models.EmailField(unique=True)

    has_registered = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_scopes(self):
        base_scopes = super().get_scopes()

        for user_type in self.user_types.all():
            base_scopes.extend(user_type.get_scopes())

        base_scopes.append(f"user:{self.id}")
        return base_scopes

    def get_name_or_username(self):
        return self.get_full_name() or self.username

    def clean(self):
        self.username = self.username.lower()
        self.email = self.email.lower()

    def __str__(self):
        return "User %s" % (self.username,)


class UserType(HasScopedPermissionsMixin, ScopedModelMixin, models.Model):
    class Meta:
        pass

    name = models.CharField(max_length=128)

    company = models.ForeignKey(
        "companies.Company", on_delete=models.CASCADE, related_name="user_types"
    )
    users = models.ManyToManyField("users.User", blank=True, related_name="user_types")
    permissions = models.ManyToManyField(Permission, blank=True)
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
