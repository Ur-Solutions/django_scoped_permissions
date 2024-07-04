from django.test import TestCase

from django_scoped_permissions.core.create_scoped_permission import create_scoped_permission


class TestCreateScopedPermission(TestCase):

    def test_single_scope(self):

        permission = create_scoped_permission("user")
        self.assertEqual(permission, "user")

    def test_simple_multiple_scope_single_arg(self):
        permissions = create_scoped_permission("user:1")

        self.assertEqual(permissions, "user:1")

    def test_simple_multiple_scope_multiple_args(self):
        permissions = create_scoped_permission("user", "1")

        self.assertEqual(permissions, "user:1")

    def test_named_arguments_for_scope_and_verb(self):
        permissions = create_scoped_permission(scope="user", verb="read")

        self.assertEqual(permissions, "user@read")
