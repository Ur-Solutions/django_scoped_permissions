from django.test import TestCase
from .scoped_permission import sp


class TestCreateScopedPermission(TestCase):

    def test_single_scope(self):

        permission = sp("user")
        self.assertEqual(permission.scope, "user")

    def test_simple_multiple_scope_single_arg(self):
        permissions = sp("user:1")

        self.assertEqual(permissions.scope, "user:1")

    def test_simple_multiple_scope_multiple_args(self):
        permissions = sp("user", "1")

        self.assertEqual(permissions.scope, "user:1")

    def test_named_arguments_for_scope_and_verb(self):
        permissions = sp(scope="user", verb="read")

        self.assertEqual(permissions.scope, "user")
        self.assertEqual(permissions.verb, "read")

    def test_embedded_verb(self):
        permissions = sp("user@read")

        self.assertEqual(permissions.scope, "user")
        self.assertEqual(permissions.verb, "read")

    def test_is_negation_from_kwargs(self):
        permissions = sp("user", is_negation=True)

        self.assertEqual(permissions.scope, "user")
        self.assertTrue(permissions.is_negation)

    def test_is_exact_from_kwargs(self):
        permissions = sp("user", is_exact=True)

        self.assertTrue(permissions.is_exact)

    def test_embedded_is_negation(self):
        permissions = sp("-user:1@verb")

        self.assertEqual(permissions.scope, "user:1")
        self.assertEqual(permissions.verb, "verb")
        self.assertTrue(permissions.is_negation)

    def test_embedded_is_exact(self):
        permissions = sp("=user:1@verb")

        self.assertEqual(permissions.scope, "user:1")
        self.assertEqual(permissions.verb, "verb")
        self.assertTrue(permissions.is_exact)

    def test_embedded_both_is_negation_and_exact(self):
        permissions = sp("-=user:1@verb")

        self.assertEqual(permissions.scope, "user:1")
        self.assertEqual(permissions.verb, "verb")
        self.assertTrue(permissions.is_negation)
        self.assertTrue(permissions.is_exact)
