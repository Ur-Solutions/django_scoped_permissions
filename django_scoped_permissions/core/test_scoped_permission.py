from django.test import TestCase
from django_scoped_permissions.core.scoped_permission import sp, ScopedPermission


class TestCreateScopedPermission(TestCase):

    def test_creates_instance_of_scoped_permission(self):
        permission = ScopedPermission.create("user")
        self.assertIsInstance(permission, ScopedPermission)

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


class TestCheckAccess(TestCase):

    def test_check_access_exact_match(self):
        required_permission = ScopedPermission.create('=foo')
        granting_permission = ScopedPermission.create('foo')

        self.assertTrue(required_permission.check_access(granting_permission))

    def test_check_access_granting_permission_exact_match(self):
        required_permission = ScopedPermission.create('foo')
        granting_permission = ScopedPermission.create('=foo')

        self.assertTrue(required_permission.check_access(granting_permission))

    def test_check_access_granting_permission_exact_does_not_match(self):
        required_permission = ScopedPermission.create('foo')
        granting_permission = ScopedPermission.create('=bar')

        self.assertFalse(required_permission.check_access(granting_permission))

    def test_check_access_granting_permission_not_exact_does_not_match(self):
        required_permission = ScopedPermission.create('foo')
        granting_permission = ScopedPermission.create('bar')

        self.assertFalse(required_permission.check_access(granting_permission))

    def test_check_access_granting_permission_contains_required_permission(self):
        required_permission = ScopedPermission.create('foo:bar')
        granting_permission = ScopedPermission.create('foo')

        self.assertTrue(required_permission.check_access(granting_permission))

    def test_check_access_required_permission_contains_granting_permission(self):
        required_permission = ScopedPermission.create('foo')
        granting_permission = ScopedPermission.create('foo:bar')

        self.assertFalse(required_permission.check_access(granting_permission))

    def test_check_access_negations_match(self):
        required_permission = ScopedPermission.create('foo')
        granting_permission = ScopedPermission.create('-foo')

        self.assertFalse(required_permission.check_access(granting_permission))

        required_permission = ScopedPermission.create('-foo')
        granting_permission = ScopedPermission.create('foo')

        self.assertFalse(required_permission.check_access(granting_permission))

        required_permission = ScopedPermission.create('-foo')
        granting_permission = ScopedPermission.create('-foo')

        self.assertFalse(required_permission.check_access(granting_permission))

    def test_check_access_scopes_and_verbs_match(self):
        required_permissions = ScopedPermission.create('foo@bar')
        granting_permissions = ScopedPermission.create('foo@bar')

        self.assertTrue(required_permissions.check_access(granting_permissions))

    def test_check_access_verbs_do_not_match(self):
        required_permissions = ScopedPermission.create('foo@bar')
        granting_permissions = ScopedPermission.create('foo@baz')

        self.assertFalse(required_permissions.check_access(granting_permissions))

    def test_check_access_nested_verbs(self):
        required_permissions = ScopedPermission.create('foo@bar:baz')
        granting_permissions = ScopedPermission.create('foo@bar')

        self.assertTrue(required_permissions.check_access(granting_permissions))

    def test_check_access_multiple_granting_permissions_and_exclusion_matches(self):
        required_permissions = ScopedPermission.create('foo')
        granting_permissions = [
            ScopedPermission.create('foo'),
            ScopedPermission.create('-foo'),
        ]

        self.assertFalse(required_permissions.check_access(granting_permissions))

    def test_check_access_include_exact_matches_exclusion(self):
        required_permissions = ScopedPermission.create('foo')
        granting_permissions = [
            ScopedPermission.create('foo'),
            ScopedPermission.create('=foo'),
            ScopedPermission.create('-foo'),
        ]

        self.assertTrue(required_permissions.check_access(granting_permissions))

    def test_check_access_exclude_exact_matches_inclusion(self):
        required_permissions = ScopedPermission.create('-foo')
        print("Test:", type(required_permissions), isinstance(required_permissions, ScopedPermission))
        granting_permissions = [
            ScopedPermission.create('foo'),
            ScopedPermission.create('=foo'),
            ScopedPermission.create('-foo'),
            ScopedPermission.create('-=foo')
        ]

        self.assertFalse(required_permissions.check_access(granting_permissions))

    def test_check_access_verb_attached_only_required_permission(self):
        required_permissions = ScopedPermission.create('foo@bar')
        granting_permissions = ScopedPermission.create("foo")

        self.assertTrue(required_permissions.check_access(granting_permissions))

    def test_check_access_verb_on_higher_level_scope(self):
        required_permissions = ScopedPermission.create('users:1:emergencycontacts@update')
        granting_permissions = ScopedPermission.create('users@update')

        self.assertTrue(required_permissions.check_access(granting_permissions))