from django.test import TestCase

from django_scoped_permissions.guards import ScopedPermissionGuard


class TestScopedPermissionGuard(TestCase):
    def test__guard_with_scope__grants_and_denies_access_correctly(self):
        guard = ScopedPermissionGuard("scope1:scope2")

        self.assertTrue(guard.has_permission("scope1"))
        self.assertFalse(guard.has_permission("scope2"))
        self.assertTrue(guard.has_permission("scope1:scope2"))
        self.assertFalse(guard.has_permission("scope"))

    def test__guard_with_multiple_scopes__grants_and_denies_access_with_OR_functionality(
        self,
    ):
        guard = ScopedPermissionGuard("scope1:scope2", "scope3:scope4")

        self.assertTrue(guard.has_permission("scope1"))
        self.assertFalse(guard.has_permission("scope2"))
        self.assertTrue(guard.has_permission("scope1:scope2"))
        self.assertFalse(guard.has_permission("scope"))

        self.assertTrue(guard.has_permission("scope3"))
        self.assertFalse(guard.has_permission("scope4"))
        self.assertTrue(guard.has_permission("scope3:scope4"))
        self.assertFalse(guard.has_permission("scope"))

    def test__guard_with_action_and_verb__grants_and_denies_access_correctly(self):
        guard = ScopedPermissionGuard(scope="scope1:scope2", verb="read")

        self.assertTrue(guard.has_permission("scope1:read"))
        self.assertFalse(guard.has_permission("scope2:read"))
        self.assertTrue(guard.has_permission("scope1:scope2:read"))
        self.assertFalse(guard.has_permission("scope:read"))

        self.assertTrue(guard.has_permission("scope1"))
        self.assertFalse(guard.has_permission("scope2"))
        self.assertTrue(guard.has_permission("scope1:scope2"))
        self.assertFalse(guard.has_permission("scope"))

    def test__and_operator__grants_and_denies_acceess_correctly(self):
        guard_one = ScopedPermissionGuard(scope="scope1:scope2", verb="read")
        guard_two = ScopedPermissionGuard(scope="scope3:scope4")

        guard = guard_one & guard_two

        self.assertTrue(guard.has_permission(["scope1:read", "scope3"]))
        self.assertFalse(guard.has_permission(["scope1:read"]))
        self.assertTrue(guard.has_permission(["scope1:scope2:read", "scope3:scope4"]))
        self.assertTrue(guard.has_permission(["scope1", "scope3"]))
        self.assertFalse(guard.has_permission("scope1"))
        self.assertFalse(guard.has_permission("scope2"))

    def test__or_operator__grants_and_denies_acceess_correctly(self):
        guard_one = ScopedPermissionGuard(scope="scope1:scope2", verb="read")
        guard_two = ScopedPermissionGuard(scope="scope3:scope4")

        guard = guard_one | guard_two

        self.assertTrue(guard.has_permission(["scope1:read", "scope3"]))
        self.assertTrue(guard.has_permission(["scope1:read"]))
        self.assertTrue(guard.has_permission(["scope1:scope2:read", "scope3:scope4"]))
        self.assertTrue(guard.has_permission(["scope1", "scope3"]))
        self.assertTrue(guard.has_permission("scope1"))

        self.assertFalse(guard.has_permission("scope4"))
        self.assertFalse(guard.has_permission("scope2"))

    def test__xor_operator__grants_and_denies_acceess_correctly(self):
        guard_one = ScopedPermissionGuard(scope="scope1:scope2", verb="read")
        guard_two = ScopedPermissionGuard(scope="scope3:scope4")

        guard = guard_one ^ guard_two

        self.assertFalse(guard.has_permission(["scope1:read", "scope3"]))
        self.assertTrue(guard.has_permission(["scope1:read"]))
        self.assertFalse(guard.has_permission(["scope1:scope2:read", "scope3:scope4"]))
        self.assertFalse(guard.has_permission(["scope1", "scope3"]))
        self.assertTrue(guard.has_permission("scope1"))

        self.assertFalse(guard.has_permission("scope4"))
        self.assertFalse(guard.has_permission("scope2"))

    def test__not_operator__grants_and_denies_access_correctly(self):
        guard_one = ScopedPermissionGuard(scope="scope1:scope2", verb="read")

        guard = ~guard_one

        self.assertFalse(guard.has_permission("scope1:read"))
        self.assertTrue(guard.has_permission("scope2:read"))
        self.assertFalse(guard.has_permission("scope1:scope2:read"))
        self.assertTrue(guard.has_permission("scope:read"))

        self.assertFalse(guard.has_permission("scope1"))
        self.assertTrue(guard.has_permission("scope2"))
        self.assertFalse(guard.has_permission("scope1:scope2"))
        self.assertTrue(guard.has_permission("scope"))

    def test__guard_with_context__is_expanded_and_checked(self):
        guard = ScopedPermissionGuard("scope1:{var}")

        self.assertTrue(guard.has_permission("scope1", context={}))
        self.assertTrue(
            guard.has_permission("scope1:scope2", context={"var": "scope2"})
        )
        self.assertTrue(
            guard.has_permission(
                "scope1:scope3",
                context={"var": ["scope2", "scope3"], "other": ["scope4"]},
            )
        )

    def test__guard_with_empty_list__returns_always_false_guard(self):
        guard = ScopedPermissionGuard([])
        self.assertFalse(guard.has_permission("something"))
        self.assertFalse(guard.has_permission("something:else"))
        self.assertFalse(guard.has_permission("anything?"))
