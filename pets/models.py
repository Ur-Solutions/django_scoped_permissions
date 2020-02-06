from django.db import models

from permissions.models import ScopedModelMixin


class Pet(ScopedModelMixin, models.Model):
    class Meta:
        pass

    company = models.ForeignKey("companies.Company", on_delete=models.CASCADE)
    user = models.ForeignKey("users.User", on_delete=models.CASCADE)

    name = models.CharField(max_length=128)
    age = models.PositiveIntegerField()

    def get_base_scopes(self):
        return [
            create_scope("pet", self.id),
            create_scope("user", self.user.id, "pet", self.id),
            create_scope("company", self.company.id, "pet", self.id),
        ]

    def __str__(self):
        return self.name
