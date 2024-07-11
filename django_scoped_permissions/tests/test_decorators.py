import graphene
from addict import Dict
from django.core.exceptions import PermissionDenied
from django.test import TestCase

from django_scoped_permissions.decorators import protect_view
from django_scoped_permissions.tests.factories import UserFactory


class TestProtectView(TestCase):

    def test_simple_protection_with_string(self):
        @protect_view("user:1@read")
        def some_function(request):
            return True

        user = UserFactory.create()
        user.add_or_create_permission("user:1@read")
        context = Dict(user=user)

        result = some_function(request=context)
        self.assertTrue(result)

    def test_simple_protection_fails(self):
        @protect_view("user:2@read")
        def some_function(request):
            return True

        user = UserFactory.create(id=1)
        context = Dict(user=user)

        with self.assertRaises(PermissionDenied):
            some_function(request=context)

    def test_custom_resolve_context(self):
        @protect_view("user:{id}@read", resolve_context=lambda request: {"id": 25})
        def some_function(request):
            return True

        user = UserFactory.create()
        user.add_or_create_permission("user:25@read")
        context = Dict(user=user)

        result = some_function(request=context)
        self.assertTrue(result)

        @protect_view("user:{id}@read", resolve_context=lambda request: {"id": 24})
        def some_other_function(request):
            return False

        with self.assertRaises(PermissionDenied):
            result = some_other_function(request=context)

    def test_custom_fn(self):

        def check_access(request):
            print(request.user.id)
            return request.user.id == 1

        @protect_view(fn=check_access)
        def some_function(request):
            return True

        user = UserFactory.create(id=1)
        context = Dict(user=user)

        result = some_function(request=context)
        self.assertTrue(result)

        def check_stricter_access(request):
            return request.user.is_superuser

        @protect_view(fn=check_stricter_access)
        def some_other_function(request):
            return False

        with self.assertRaises(PermissionDenied):
            result = some_other_function(request=context)

