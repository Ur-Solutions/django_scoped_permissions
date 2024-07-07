from django.test import TestCase

from django_scoped_permissions.core.check_scoped_permission import check_scoped_permission


class TestCheckScopedPermissionWithSingularArguments(TestCase):

    def test_single_scope_equality__returns_true(self):
        self.assertTrue(check_scoped_permission(required_permission="user", granting_permission="user"))

    def test_single_scope_equality__returns_false(self):
        self.assertFalse(check_scoped_permission(required_permission="user", granting_permission="group"))

    def test_single_scope_with_verb__returns_true(self):
        self.assertTrue(check_scoped_permission(required_permission="user@read", granting_permission="user@read"))

    def test_multiple_scope_equality__returns_true(self):
        self.assertTrue(check_scoped_permission(required_permission="user:1", granting_permission="user:1"))

    def test_permission_with_higher_level_scope__returns_true(self):
        self.assertTrue(check_scoped_permission(required_permission="user:1", granting_permission="user:1"))

    def test_permission_with_higher_level_scope_and_verb__returns_true(self):
        self.assertTrue(check_scoped_permission(required_permission="user:1@read", granting_permission="user:1"))
        self.assertTrue(check_scoped_permission(required_permission="user:1@read", granting_permission="user"))
