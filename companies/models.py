from django.db import models


class Company(models.Model):
    class Meta:
        pass

    name = models.CharField(max_length=128)
    short_name = models.CharField(max_length=32)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    users = models.ManyToManyField("users.User", related_name="companies")

    email = models.CharField(max_length=256, null=True, blank=True)
