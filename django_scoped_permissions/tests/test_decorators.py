from addict import Dict
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from django_scoped_permissions.decorators import gql_has_scoped_permissions
from django_scoped_permissions.models import ScopedPermission
from django_scoped_permissions.tests.factories import UserFactory, CompanyFactory


class TestSqlHasScopedPermissions(TestCase):
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
