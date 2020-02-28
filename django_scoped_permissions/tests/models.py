from django.contrib.auth.models import AbstractUser
from django.db import models

from django_scoped_permissions.models import HasScopedPermissionsMixin, ScopedModelMixin
from django_scoped_permissions.util import create_scope


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


class UserType(HasScopedPermissionsMixin, ScopedModelMixin, models.Model):
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

    def get_base_scopes(self):
        return [
            create_scope("pet", self.id),
            create_scope("user", self.user.id, "pet", self.id),
        ]

    def __str__(self):
        return self.name


class Building(ScopedModelMixin, models.Model):
    class Meta:
        pass

    name = models.CharField(max_length=128)

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    company = models.ForeignKey(
        Company, related_name="buildings", on_delete=models.CASCADE
    )
    users = models.ManyToManyField(User, related_name="buildings")

    def get_base_scopes(self):
        scopes = [
            create_scope(Company, self.company.id, self, self.id),
        ]
        if self.created_by is not None:
            scopes.append(create_scope(User, self.created_by.id, self, self.id))

        return scopes

    def __str__(self):
        return self.name