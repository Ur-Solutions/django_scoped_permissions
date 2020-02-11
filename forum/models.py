from django.db import models

from permissions.models import ScopedModelMixin
from permissions.util import create_scope
from users.models import User


class Thread(ScopedModelMixin, models.Model):
    class Meta:
        pass

    title = models.CharField(max_length=256)
    text = models.TextField()

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=False, related_name="threads",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def get_base_scopes(self):
        return [
            create_scope(self, self.id),
            create_scope(User, self.created_by.id, self, self.id),
        ]

    def __str__(self):
        user_name = (
            self.created_by.get_name_or_username() if self.created_by else "[deleted]"
        )
        return f"{self.title} by {user_name}"


class Post(ScopedModelMixin, models.Model):
    class Meta:
        pass

    thread = models.ForeignKey(Thread, related_name="posts", on_delete=models.CASCADE)

    text = models.TextField()

    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=False, related_name="posts",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    def get_base_scopes(self):
        return [
            create_scope(self, self.id),
            create_scope(User, self.created_by.id, self, self.id),
        ]
