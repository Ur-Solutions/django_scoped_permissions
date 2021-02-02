from addict import Dict
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from django_scoped_permissions.core import scopes_grant_permissions
from django_scoped_permissions.tests.factories import UserFactory

from django_scoped_permissions.decorators import (
    gql_has_scoped_permissions,
)
from django_scoped_permissions.models import ScopedPermission
from django_scoped_permissions.tests.factories import PetFactory


class TestScopesGrantPermission(TestCase):
    def test__equal_scopes_match__returns_true(self):
        scopes = ["scope1:action"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(scopes_grant_permissions(required_scopes, scopes), True)

    def test__scope_contained_in_required__returns_true(self):
        scopes = ["scope1"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(scopes_grant_permissions(required_scopes, scopes), True)

    def test__no_matching_scope__returns_false(self):
        scopes = ["scope3"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(scopes_grant_permissions(required_scopes, scopes), False)

    def test__scoped_has_negation__invalidates_and_returns_false(self):
        scopes = ["scope1", "-scope1:action"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(scopes_grant_permissions(required_scopes, scopes), False)

    def test__scoped_has_high_level_negation__invalidates_and_returns_false(self):
        scopes = ["scope1:action", "-scope1"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(scopes_grant_permissions(required_scopes, scopes), False)

    def test__scoped_has_exact_operator__returns_true_on_exact_match(self):
        scopes = ["=scope1:action"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(scopes_grant_permissions(required_scopes, scopes), True)

    def test__scoped_has_exact_operator__returns_false_on_exact_match(self):
        scopes = ["=scope1"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(scopes_grant_permissions(required_scopes, scopes), False)

    def test__scoped_has_exact_operator_and_negation__returns_false_on_exact_match(
        self,
    ):
        scopes = ["-=scope1:action"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(scopes_grant_permissions(required_scopes, scopes), False)

    def test__scoped_has_exact_operator_and_negation__returns_true_on_hierarchical_match(
        self,
    ):
        scopes = [
            "scope1:action",
            "-=scope1",
        ]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(scopes_grant_permissions(required_scopes, scopes), True)


class TestHasScopedPermissionsMixin(TestCase):
    def get_scopes__no_scopes__returns_empty_array(self):
        user = UserFactory.create()

        # Users automatically get the user:1 scope
        self.assertListEqual(user.get_granting_scopes(), ["user:1"])

    def test_get_scopes__simple_scopes__returns_array(self):
        user = UserFactory.create()
        user.scoped_permissions.add(
            ScopedPermission.objects.create(scope="simple:scope")
        )
        user.scoped_permissions.add(
            ScopedPermission.objects.create(scope="simple:scope:deep")
        )

        # Users automatically get the user:1 scope
        self.assertListEqual(
            user.get_granting_scopes(), ["simple:scope", "simple:scope:deep", "user:1"]
        )

    def test_get_scopes__exclude_scopes__appends_minus_signs(self):
        user = UserFactory.create()
        user.scoped_permissions.add(
            ScopedPermission.objects.create(scope="simple:scope", exclude=True)
        )
        user.scoped_permissions.add(
            ScopedPermission.objects.create(scope="simple:scope:deep", exclude=True)
        )

        # Users automatically get the user:1 scope
        self.assertListEqual(
            user.get_granting_scopes(),
            ["-simple:scope", "-simple:scope:deep", "user:1"],
        )

    def test_get_scopes__exact_scopes__appends_equal_sign(self):
        user = UserFactory.create()
        user.scoped_permissions.add(
            ScopedPermission.objects.create(scope="simple:scope", exact=True)
        )
        user.scoped_permissions.add(
            ScopedPermission.objects.create(scope="simple:scope:deep", exact=True)
        )

        # Users automatically get the user:1 scope
        self.assertListEqual(
            user.get_granting_scopes(),
            ["=simple:scope", "=simple:scope:deep", "user:1"],
        )

    def test_get_scopes__exact_and_negation_scopes__appends_equal_and_minus_sign(self):
        user = UserFactory.create()
        user.scoped_permissions.add(
            ScopedPermission.objects.create(
                scope="simple:scope", exclude=True, exact=True
            )
        )
        user.scoped_permissions.add(
            ScopedPermission.objects.create(
                scope="simple:scope:deep", exclude=True, exact=True
            )
        )

        # Users automatically get the user:1 scope
        self.assertListEqual(
            user.get_granting_scopes(),
            ["-=simple:scope", "-=simple:scope:deep", "user:1"],
        )


class TestScopedModelMixin(TestCase):
    def test_has_permission__user_has_exclude_on_specific_parent_scope__does_not_cascade(
        self,
    ):
        user = UserFactory.create()
        user.scoped_permissions.add(
            ScopedPermission.objects.create(
                scope="user:1", exclude=True, exact=True
            )
        )

        pet = PetFactory.create(user=user)
        self.assertTrue(pet.has_permission(user, "update"))

    def test_has_permission__user_has_exclude_on_specific_top_level_scope_without_action__does_not_cascade(
        self,
    ):
        user = UserFactory.create()
        user.scoped_permissions.add(
            ScopedPermission.objects.create(scope="user", exclude=True, exact=True)
        )

        pet = PetFactory.create(user=user)
        self.assertTrue(pet.has_permission(user))


class TestGqlHasScopedPermissions(TestCase):
    def test__user_has_permission__succeeds(self):
        @gql_has_scoped_permissions("simple:scope")
        def wrapper_method(cls, info, *args, **kwargs):
            return True

        user = UserFactory.create()
        user.scoped_permissions.add(
            ScopedPermission.objects.create(scope="simple:scope")
        )

        info = Dict(context=Dict(user=user))

        result = wrapper_method(None, info)
        self.assertTrue(result)

    def test__user_does_not_have_permission__fails(self):
        @gql_has_scoped_permissions("simple:scope")
        def wrapper_method(cls, info, *args, **kwargs):
            return True

        user = UserFactory.create()
        user.scoped_permissions.add(
            ScopedPermission.objects.create(scope="simple:scope:nested")
        )

        info = Dict(context=Dict(user=user))

        with self.assertRaises(PermissionDenied):
            wrapper_method(None, info)

