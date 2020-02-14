from django.test import TestCase

# Create your tests here.
from graphene_django_cud.tests.factories import UserFactory

from permissions.models import ScopedPermission
from permissions.util import any_scope_matches
from pets.models import Pet
from users.models import User


class TestAnyScopeMatches(TestCase):
    def test__equal_scopes_match__returns_true(self):
        scopes = ["scope1:action"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(any_scope_matches(required_scopes, scopes), True)

    def test__scope_contained_in_required__returns_true(self):
        scopes = ["scope1"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(any_scope_matches(required_scopes, scopes), True)

    def test__no_matching_scope__returns_false(self):
        scopes = ["scope3"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(any_scope_matches(required_scopes, scopes), False)

    def test__scoped_has_negation__invalidates_and_returns_false(self):
        scopes = ["scope1", "-scope1:action"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(any_scope_matches(required_scopes, scopes), False)

    def test__scoped_has_high_level_negation__invalidates_and_returns_false(self):
        scopes = ["scope1:action", "-scope1"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(any_scope_matches(required_scopes, scopes), False)

    def test__scoped_has_exact_operator__returns_true_on_exact_match(self):
        scopes = ["=scope1:action"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(any_scope_matches(required_scopes, scopes), False)

    def test__scoped_has_exact_operator__returns_false_on_exact_match(self):
        scopes = ["=scope1"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(any_scope_matches(required_scopes, scopes), False)

    def test__scoped_has_exact_operator_and_negation__returns_false_on_exact_match(
        self,
    ):
        scopes = ["-=scope1:action"]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(any_scope_matches(required_scopes, scopes), False)

    def test__scoped_has_exact_operator_and_negation__returns_true_on_hierarchical_match(
        self,
    ):
        scopes = [
            "scope1:action",
            "-=scope1",
        ]
        required_scopes = ["scope2", "scope1:action"]
        self.assertEqual(any_scope_matches(required_scopes, scopes), True)

