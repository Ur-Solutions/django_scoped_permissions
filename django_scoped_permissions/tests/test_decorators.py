from addict import Dict
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from django_scoped_permissions.decorators import gql_has_scoped_permissions
from django_scoped_permissions.guards import ScopedPermissionGuard
from django_scoped_permissions.models import ScopedPermission
from django_scoped_permissions.tests.factories import UserFactory, CompanyFactory


class TestGqlHasScopedPermissions(TestCase):
    def test__simple_scope_check_with_permission__permits(self):
        @gql_has_scoped_permissions("scope1:scope2")
        def wrapper_method(self, info):
            pass

        user = UserFactory.create()
        perm = ScopedPermission.objects.create(scope="scope1:scope2")
        user.scoped_permissions.add(perm)
        info = Dict()
        info.context.user = user
        wrapper_method(None, info)

    def test__simple_scope_check_without_permission__fails(self):
        @gql_has_scoped_permissions("scope1:scope2")
        def wrapper_method(self, info):
            pass

        user = UserFactory.create()
        perm = ScopedPermission.objects.create(scope="scope3")
        user.scoped_permissions.add(perm)
        info = Dict()
        info.context.user = user
        with self.assertRaises(PermissionDenied):
            wrapper_method(None, info)

    def test_expand_from_context__check_with_organization__succeeds(self):
        @gql_has_scoped_permissions("company:{context.company.id}:read")
        def wrapper_method(self, info):
            pass

        user = UserFactory.create()
        perm = ScopedPermission.objects.create(scope="company:1")
        user.scoped_permissions.add(perm)
        info = Dict()
        info.context.user = user
        info.context.company = CompanyFactory.create()
        wrapper_method(None, info)

    def test__multiple_permisions__becomes_or_statement_by_default(self):
        @gql_has_scoped_permissions("scope1", "scope2")
        def wrapper_method(self, info):
            pass

        user = UserFactory.create()
        perm = ScopedPermission.objects.create(scope="scope1")
        user.scoped_permissions.add(perm)

        info = Dict()
        info.context.user = user
        info.context.company = CompanyFactory.create()
        wrapper_method(None, info)

        user.scoped_permissions.all().delete()
        perm = ScopedPermission.objects.create(scope="scope2")
        user.scoped_permissions.add(perm)
        wrapper_method(None, info)

        with self.assertRaises(PermissionDenied):
            user.scoped_permissions.all().delete()
            perm = ScopedPermission.objects.create(scope="scope3")
            user.scoped_permissions.add(perm)
            wrapper_method(None, info)

    def test__with_guard__uses_guard(self):
        @gql_has_scoped_permissions(ScopedPermissionGuard("scope1"))
        def wrapper_method(self, info):
            pass

        user = UserFactory.create()
        perm = ScopedPermission.objects.create(scope="scope1")
        user.scoped_permissions.add(perm)

        info = Dict()
        info.context.user = user
        info.context.company = CompanyFactory.create()
        wrapper_method(None, info)

    def test__with_verb_and_scope__uses_verb_and_scope(self):
        @gql_has_scoped_permissions(scope="scope1", verb="verb")
        def wrapper_method(self, info):
            pass

        user = UserFactory.create()
        perm = ScopedPermission.objects.create(scope="scope1:verb")
        user.scoped_permissions.add(perm)

        info = Dict()
        info.context.user = user
        info.context.company = CompanyFactory.create()
        wrapper_method(None, info)

        user.scoped_permissions.all().delete()
        perm = ScopedPermission.objects.create(scope="verb")
        user.scoped_permissions.add(perm)
        wrapper_method(None, info)

    def test__with_verb_and_scope__uses_verb_and_scope(self):
        @gql_has_scoped_permissions(scope="scope1", verb="verb")
        def wrapper_method(self, info):
            pass

        user = UserFactory.create()
        perm = ScopedPermission.objects.create(scope="scope1:verb")
        user.scoped_permissions.add(perm)

        info = Dict()
        info.context.user = user
        info.context.company = CompanyFactory.create()
        wrapper_method(None, info)

        user.scoped_permissions.all().delete()
        perm = ScopedPermission.objects.create(scope="verb")
        user.scoped_permissions.add(perm)
        wrapper_method(None, info)

    def test__complex_permission_guard_combination__uses_guard(self):
        # Matches when a user has scope1 and not scope2:read (or just read) OR
        # when the user has scope2:scope3 xor scope4
        @gql_has_scoped_permissions(
            (
                ScopedPermissionGuard("scope1")
                & ~ScopedPermissionGuard(scope="scope2", verb="read")
            )
            | (ScopedPermissionGuard("scope2:scope3") ^ ScopedPermissionGuard("scope4"))
        )
        def wrapper_method(self, info):
            pass

        user = UserFactory.create()
        perm = ScopedPermission.objects.create(scope="scope1")
        user.scoped_permissions.add(perm)

        info = Dict()
        info.context.user = user
        info.context.company = CompanyFactory.create()
        wrapper_method(None, info)

        user.scoped_permissions.all().delete()
        perm = ScopedPermission.objects.create(scope="scope2:scope3")
        user.scoped_permissions.add(perm)
        wrapper_method(None, info)

        user.scoped_permissions.all().delete()
        perm = ScopedPermission.objects.create(scope="scope4")
        user.scoped_permissions.add(perm)
        wrapper_method(None, info)

        with self.assertRaises(PermissionDenied):
            user.scoped_permissions.all().delete()
            perm = ScopedPermission.objects.create(scope="scope1")
            perm = ScopedPermission.objects.create(scope="scope2:read")
            user.scoped_permissions.add(perm)
            wrapper_method(None, info)

        with self.assertRaises(PermissionDenied):
            user.scoped_permissions.all().delete()
            user.add_or_create_permission("scope1")
            user.add_or_create_permission("read")
            wrapper_method(None, info)
