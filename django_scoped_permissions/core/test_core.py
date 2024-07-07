from django.test import TestCase

from django_scoped_permissions.core import scope_matches, scope_grants_permission


class TestScopeGrantsPermission(TestCase):
    def test__equal_scopes__returns_true(self):
        self.assertTrue(
            scope_grants_permission("user:1", "user:1")
        )

    def test__required_scope_starts_with_granting_scope__returns_true(self):
        self.assertTrue(
            scope_grants_permission("user:1:edit", "user:1")
        )
        self.assertTrue(
            scope_grants_permission("organization:edit:user", "organization:edit")
        )

    def test__required_scope_ends_with_granting_scope__returns_false(self):
        self.assertFalse(
            scope_grants_permission("organization:user:1", "user:1")
        )

    def test__granting_scope_is_substring_but_does_not_match_parent_scope__returns_false(self):
        self.assertTrue(
            scope_grants_permission("user:1:edit", "user")
        )
        self.assertFalse(
            scope_grants_permission("organization:edit:user", "organization:ed")
        )

    def test__exact_scope_matches_only_on_exact_match(self):
        self.assertTrue(
            scope_grants_permission("user:1", "=user:1")
        )
        self.assertFalse(
            scope_grants_permission("user:1:update", "=user:1")
        )

    def test__exclusive_scope__always_fails(self):
        self.assertFalse(
            scope_grants_permission("user:1", "-user:1")
        )
        self.assertFalse(
            scope_grants_permission("user:1:subscope", "-user:1")
        )
        self.assertFalse(
            scope_grants_permission("user:1", "-read", "read")
        )


class TestScopeMatches(TestCase):
    def test__equal_scopes__returns_true(self):
        self.assertTrue(
            scope_matches("user:1", "user:1")
        )

    def test__required_scope_starts_with_granting_scope__returns_true(self):
        self.assertTrue(
            scope_matches("user:1:edit", "user:1")
        )
        self.assertTrue(
            scope_matches("organization:edit:user", "organization:edit")
        )

    def test__required_scope_ends_with_granting_scope__returns_false(self):
        self.assertFalse(
            scope_matches("organization:user:1", "user:1")
        )

    def test__granting_scope_is_substring_but_does_not_match_parent_scope__returns_false(self):
        self.assertFalse(
            scope_matches("user:1:edit", "use")
        )
        self.assertFalse(
            scope_matches("organization:edit:user", "organization:ed")
        )

    def test__wildcard_on_granting_scope__matches(self):
        self.assertTrue(
            scope_matches("user:1:edit", "*")
        )
        self.assertTrue(
            scope_matches("organization:edit:user", "*")
        )
        self.assertTrue(
            scope_matches("organization:edit:user", "organization:*")
        )
        self.assertTrue(
            scope_matches("organization:edit:user", "organization:*:user")
        )
        self.assertTrue(
            scope_matches("organization:edit:user", "*:edit:user")
        )
        self.assertTrue(
            scope_matches("organization:edit:user", "organization:*:user")
        )
        self.assertFalse(
            scope_matches("organization:edit:user", "organization:edit:user:*")
        )
        self.assertFalse(
            scope_matches("organization:edit:user", "*:edit:user:*")
        )

    def test__wildcard_on_required__scope__matches(self):
        self.assertTrue(
            scope_matches("user:*:edit", "user:1:edit")
        )
        self.assertTrue(
            scope_matches("organization:*:user", "organization:4:user")
        )
        self.assertTrue(
            scope_matches("organization:*", "organization:clients")
        )
        self.assertFalse(
            scope_matches("organization:*", "organization:clients:read")
        )
