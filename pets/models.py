from django.db import models

from permissions.models import ScopedModelMixin
from permissions.util import create_scope


class Pet(ScopedModelMixin, models.Model):
    class Meta:
        pass

    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="pets"
    )

    name = models.CharField(max_length=128)
    age = models.PositiveIntegerField()

    def get_base_scopes(self):
        return [
            create_scope("pet", self.id),
            create_scope("user", self.user.id, "pet", self.id),
        ]

    def __str__(self):
        return self.name
