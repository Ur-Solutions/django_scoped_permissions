from django.test import TestCase

from django_scoped_permissions.models import StoredScopedPermission
from django_scoped_permissions.tests.factories import UserFactory
from django_scoped_permissions.tests.models import User


class TestHasScopedPermissionMixin(TestCase):
    def test_resolve_scopes__from_direct_m2m_field__resolves_correctly(self):
        user = UserFactory.create()

        scoped_permission_one = StoredScopedPermission.objects.create(
            scope="scope1"
        )
        scoped_permission_two = StoredScopedPermission.objects.create(
            scope="scope1:scope2"
        )
        scoped_permission_three = StoredScopedPermission.objects.create(
            scope="scope3:scope4",
            exact=True
        )
        scoped_permission_four = StoredScopedPermission.objects.create(
            scope="scope5:scope6",
            exclude=True
        )
        scoped_permission_five = StoredScopedPermission.objects.create(
            scope="scope7:scope8",
            exclude=True,
            exact=True
        )
        user.scoped_permissions.add(scoped_permission_one)
        user.scoped_permissions.add(scoped_permission_two)
        user.scoped_permissions.add(scoped_permission_three)
        user.scoped_permissions.add(scoped_permission_four)
        user.scoped_permissions.add(scoped_permission_five)

        resolved = user.resolved_scopes
        self.assertIn("scope1", resolved)
        self.assertIn("scope1:scope2", resolved)
        self.assertIn("=scope3:scope4", resolved)
        self.assertIn("-scope5:scope6", resolved)
        self.assertIn("-=scope7:scope8", resolved)

    def test_add_or_create_permission__permission_exists__adds_permissions(self):
        user: User = UserFactory.create()
        user.add_or_create_permission("scope1:scope2")
        self.assertTrue(user.has_any_scoped_permissions("scope1:scope2"))

        user.add_or_create_permission("=scope3:scope4")
        self.assertTrue(user.has_any_scoped_permissions("scope3:scope4"))
        self.assertFalse(user.has_any_scoped_permissions("scope3:scope4:test"))

        user.add_or_create_permission("scope3")
        user.add_or_create_permission("-scope3:scope4")
        self.assertTrue(user.has_any_scoped_permissions("scope3:scope5"))
        self.assertFalse(user.has_any_scoped_permissions("scope3:scope4:scope5"))

    def test_add_or_create_permission__permission_exists__reuses(self):
        permission_1 = StoredScopedPermission.objects.create(
            scope="scope1:scope2"
        )
        self.assertEqual(1, StoredScopedPermission.objects.count())
        user: User = UserFactory.create()
        user.add_or_create_permission("scope1:scope2")
        self.assertEqual(1, StoredScopedPermission.objects.count())

    def test_add_or_create_permission__permission_does_not_exist__creates_new(self):
        self.assertEqual(0, StoredScopedPermission.objects.count())
        user: User = UserFactory.create()
        user.add_or_create_permission("scope1:scope2")
        self.assertEqual(1, StoredScopedPermission.objects.count())
        permission = StoredScopedPermission.objects.filter(scope="scope1:scope2").first()
        self.assertIsNotNone(permission)

