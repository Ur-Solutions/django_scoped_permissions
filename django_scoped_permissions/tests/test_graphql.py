import graphene
from addict import Dict
from django.test import TestCase
from graphene import Node, Schema
from graphql_relay import to_global_id

from django_scoped_permissions.graphql import (
    ScopedDjangoNode,
    ScopedDjangoCreateMutation, ScopedDjangoUpdateMutation, ScopedDjangoPatchMutation,
)
from django_scoped_permissions.guards import ScopedPermissionGuard
from django_scoped_permissions.tests.factories import UserFactory
from django_scoped_permissions.tests.models import User


class TestScopedDjangoNode(TestCase):
    def test__node_without_explicit_permissions__has_default_permission_handling(
        self,
    ):
        # This registers the UserNode type
        # noinspection PyUnresolvedReferences
        class UserNode(ScopedDjangoNode):
            class Meta:
                model = User

        class Query(graphene.ObjectType):
            user = Node.Field(UserNode)

        user = UserFactory.create(first_name="Tormod", last_name="Haugland")
        user_two = UserFactory.create()

        schema = Schema(query=Query)
        query = """
            query User($id: ID!){
                user(id: $id){
                    id
                    firstName
                    lastName 
                } 
            }
        """

        result = schema.execute(
            query,
            variables={"id": to_global_id("UserNode", user.id)},
            context=Dict(user=user),
        )
        self.assertIsNone(result.errors)
        data = Dict(result.data)
        self.assertEqual("Tormod", data.user.firstName)

        # User two does not have permission by default
        result = schema.execute(
            query,
            variables={"id": to_global_id("UserNode", user.id)},
            context=Dict(user=user_two),
        )
        self.assertIsNotNone(result.errors)

        # Can be accessed by someone who has read permissions
        user_two.add_or_create_permission("user:read")
        result = schema.execute(
            query,
            variables={"id": to_global_id("UserNode", user.id)},
            context=Dict(user=user),
        )
        self.assertIsNone(result.errors)
        data = Dict(result.data)
        self.assertEqual("Tormod", data.user.firstName)

    def test__node_with_explicit_permissions__has_explicit_permission_handling(
        self,
    ):
        # This registers the UserNode type
        # noinspection PyUnresolvedReferences
        class UserNode(ScopedDjangoNode):
            class Meta:
                model = User
                node_permissions = ("user:read",)

        class Query(graphene.ObjectType):
            user = Node.Field(UserNode)

        user = UserFactory.create(first_name="Tormod", last_name="Haugland")
        user.add_or_create_permission("user:read")
        user_two = UserFactory.create()

        schema = Schema(query=Query)
        query = """
            query User($id: ID!){
                user(id: $id){
                    id
                    firstName
                    lastName 
                } 
            }
        """

        result = schema.execute(
            query,
            variables={"id": to_global_id("UserNode", user.id)},
            context=Dict(user=user),
        )
        self.assertIsNone(result.errors)
        data = Dict(result.data)
        self.assertEqual("Tormod", data.user.firstName)

        # User two does not have permission by default
        result = schema.execute(
            query,
            variables={"id": to_global_id("UserNode", user.id)},
            context=Dict(user=user_two),
        )
        self.assertIsNotNone(result.errors)

    def test__node_with_permission_guards__has_explicit_permission_handling(
        self,
    ):
        # This registers the UserNode type
        # noinspection PyUnresolvedReferences
        class UserNode(ScopedDjangoNode):
            class Meta:
                model = User
                node_permissions = ScopedPermissionGuard(scope="user", verb="read")

        class Query(graphene.ObjectType):
            user = Node.Field(UserNode)

        user = UserFactory.create(first_name="Tormod", last_name="Haugland")
        user.add_or_create_permission("user:read")
        user_two = UserFactory.create()

        schema = Schema(query=Query)
        query = """
            query User($id: ID!){
                user(id: $id){
                    id
                    firstName
                    lastName 
                } 
            }
        """

        result = schema.execute(
            query,
            variables={"id": to_global_id("UserNode", user.id)},
            context=Dict(user=user),
        )
        self.assertIsNone(result.errors)
        data = Dict(result.data)
        self.assertEqual("Tormod", data.user.firstName)

        # User two does not have permission by default
        result = schema.execute(
            query,
            variables={"id": to_global_id("UserNode", user.id)},
            context=Dict(user=user_two),
        )
        self.assertIsNotNone(result.errors)


class TestScopedCreateMutation(TestCase):
    def test__permissions_set__respects_permissions(
        self,
    ):
        # This registers the UserNode type
        # noinspection PyUnresolvedReferences
        from .schema import UserNode

        class CreateUserMutation(ScopedDjangoCreateMutation):
            class Meta:
                model = User
                exclude_fields = ("password",)
                permissions = ("user:create",)

        class Mutations(graphene.ObjectType):
            create_user = CreateUserMutation.Field()

        user = UserFactory.create()
        user.add_or_create_permission("user:create")

        schema = Schema(mutation=Mutations)
        mutation = """
            mutation CreateUser(
                $input: CreateUserInput! 
            ){
                createUser(input: $input){
                    user{
                        id
                        firstName
                        lastName
                        email
                    }
                }
            }
        """

        result = schema.execute(
            mutation,
            variables={
                "input": {
                    "username": "tormod",
                    "firstName": "Tormod",
                    "lastName": "Haugland",
                    "email": "tormod.haugland@gmail.com",
                }
            },
            context=Dict(user=user),
        )

        self.assertIsNone(result.errors)
        data = Dict(result.data)
        self.assertEqual("Tormod", data.createUser.user.firstName)
        self.assertEqual("Haugland", data.createUser.user.lastName)
        self.assertEqual("tormod.haugland@gmail.com", data.createUser.user.email)

    def test__set_permission_via_guard__respects_permission(
        self,
    ):
        # This registers the UserNode type
        # noinspection PyUnresolvedReferences
        from .schema import UserNode

        class CreateUserMutation(ScopedDjangoCreateMutation):
            class Meta:
                model = User
                exclude_fields = ("password",)
                permissions = ScopedPermissionGuard("user:create")

        class Mutations(graphene.ObjectType):
            create_user = CreateUserMutation.Field()

        user = UserFactory.create()
        user.add_or_create_permission("user:create")

        schema = Schema(mutation=Mutations)
        mutation = """
            mutation CreateUser(
                $input: CreateUserInput! 
            ){
                createUser(input: $input){
                    user{
                        id
                        firstName
                        lastName
                        email
                    }
                }
            }
        """

        result = schema.execute(
            mutation,
            variables={
                "input": {
                    "username": "tormod",
                    "firstName": "Tormod",
                    "lastName": "Haugland",
                    "email": "tormod.haugland@gmail.com",
                }
            },
            context=Dict(user=user),
        )

        self.assertIsNone(result.errors)
        data = Dict(result.data)
        self.assertEqual("Tormod", data.createUser.user.firstName)
        self.assertEqual("Haugland", data.createUser.user.lastName)
        self.assertEqual("tormod.haugland@gmail.com", data.createUser.user.email)


class TestScopedUpdateMutation(TestCase):
    def test__default_permission__uses_object_required_scopes(
            self,
    ):
        # This registers the UserNode type
        # noinspection PyUnresolvedReferences
        from .schema import UserNode

        class UpdateUserMutation(ScopedDjangoUpdateMutation):
            class Meta:
                model = User
                exclude_fields = ("password",)

        class Mutations(graphene.ObjectType):
            update_user = UpdateUserMutation.Field()

        user = UserFactory.create()
        user_two = UserFactory.create()

        schema = Schema(mutation=Mutations)
        mutation = """
            mutation UpdateUser(
                $id: ID!,
                $input: UpdateUserInput! 
            ){
                updateUser(id: $id, input: $input){
                    user{
                        id
                        firstName
                        lastName
                        email
                    }
                }
            }
        """

        result = schema.execute(
            mutation,
            variables={
                "id": to_global_id("UserNode", user.id),
                "input": {
                    "username": "tormod",
                    "firstName": "Tormod",
                    "lastName": "Haugland",
                    "email": "tormod.haugland@gmail.com",
                }
            },
            context=Dict(user=user),
        )

        self.assertIsNone(result.errors)
        data = Dict(result.data)
        self.assertEqual("Tormod", data.updateUser.user.firstName)
        self.assertEqual("Haugland", data.updateUser.user.lastName)
        self.assertEqual("tormod.haugland@gmail.com", data.updateUser.user.email)

        result = schema.execute(
            mutation,
            variables={
                "id": to_global_id("UserNode", user.id),
                "input": {
                    "username": "tormod",
                    "firstName": "Tormod",
                    "lastName": "Haugland",
                    "email": "tormod.haugland@gmail.com",
                }
            },
            context=Dict(user=user_two),
        )

        self.assertIsNotNone(result.errors)

    def test__specific_permission__respects_permission(
            self,
    ):
        # This registers the UserNode type
        # noinspection PyUnresolvedReferences
        from .schema import UserNode

        class UpdateUserMutation(ScopedDjangoUpdateMutation):
            class Meta:
                model = User
                exclude_fields = ("password",)
                permissions = ("user:update",)

        class Mutations(graphene.ObjectType):
            update_user = UpdateUserMutation.Field()

        user = UserFactory.create()
        user.add_or_create_permission("user:update")
        user_two = UserFactory.create()

        schema = Schema(mutation=Mutations)
        mutation = """
            mutation UpdateUser(
                $id: ID!,
                $input: UpdateUserInput! 
            ){
                updateUser(id: $id, input: $input){
                    user{
                        id
                        firstName
                        lastName
                        email
                    }
                }
            }
        """

        result = schema.execute(
            mutation,
            variables={
                "id": to_global_id("UserNode", user.id),
                "input": {
                    "username": "tormod",
                    "firstName": "Tormod",
                    "lastName": "Haugland",
                    "email": "tormod.haugland@gmail.com",
                }
            },
            context=Dict(user=user),
        )

        self.assertIsNone(result.errors)
        data = Dict(result.data)
        self.assertEqual("Tormod", data.updateUser.user.firstName)
        self.assertEqual("Haugland", data.updateUser.user.lastName)
        self.assertEqual("tormod.haugland@gmail.com", data.updateUser.user.email)

        result = schema.execute(
            mutation,
            variables={
                "id": to_global_id("UserNode", user.id),
                "input": {
                    "username": "tormod",
                    "firstName": "Tormod",
                    "lastName": "Haugland",
                    "email": "tormod.haugland@gmail.com",
                }
            },
            context=Dict(user=user_two),
        )

        self.assertIsNotNone(result.errors)


class TestScopedPatchMutation(TestCase):
    def test__default_permission__uses_object_required_scopes(
            self,
    ):
        # This registers the UserNode type
        # noinspection PyUnresolvedReferences
        from .schema import UserNode

        class PatchUserMutation(ScopedDjangoPatchMutation):
            class Meta:
                model = User
                exclude_fields = ("password",)

        class Mutations(graphene.ObjectType):
            patch_user = PatchUserMutation.Field()

        user = UserFactory.create()
        user_two = UserFactory.create()

        schema = Schema(mutation=Mutations)
        mutation = """
            mutation PatchUser(
                $id: ID!,
                $input: PatchUserInput! 
            ){
                patchUser(id: $id, input: $input){
                    user{
                        id
                        firstName
                        lastName
                        email
                    }
                }
            }
        """

        result = schema.execute(
            mutation,
            variables={
                "id": to_global_id("UserNode", user.id),
                "input": {
                    "username": "tormod",
                    "firstName": "Tormod",
                    "lastName": "Haugland",
                    "email": "tormod.haugland@gmail.com",
                }
            },
            context=Dict(user=user),
        )

        self.assertIsNone(result.errors)
        data = Dict(result.data)
        self.assertEqual("Tormod", data.patchUser.user.firstName)
        self.assertEqual("Haugland", data.patchUser.user.lastName)
        self.assertEqual("tormod.haugland@gmail.com", data.patchUser.user.email)

        result = schema.execute(
            mutation,
            variables={
                "id": to_global_id("UserNode", user.id),
                "input": {
                    "username": "tormod",
                    "firstName": "Tormod",
                    "lastName": "Haugland",
                    "email": "tormod.haugland@gmail.com",
                }
            },
            context=Dict(user=user_two),
        )

        self.assertIsNotNone(result.errors)

    def test__specific_permission__respects_permission(
            self,
    ):
        # This registers the UserNode type
        # noinspection PyUnresolvedReferences
        from .schema import UserNode

        class PatchUserMutation(ScopedDjangoPatchMutation):
            class Meta:
                model = User
                exclude_fields = ("password",)
                permissions = ("user:patch",)

        class Mutations(graphene.ObjectType):
            patch_user = PatchUserMutation.Field()

        user = UserFactory.create()
        user.add_or_create_permission("user:patch")
        user_two = UserFactory.create()

        schema = Schema(mutation=Mutations)
        mutation = """
            mutation PatchUser(
                $id: ID!,
                $input: PatchUserInput! 
            ){
                patchUser(id: $id, input: $input){
                    user{
                        id
                        firstName
                        lastName
                        email
                    }
                }
            }
        """

        result = schema.execute(
            mutation,
            variables={
                "id": to_global_id("UserNode", user.id),
                "input": {
                    "username": "tormod",
                    "firstName": "Tormod",
                    "lastName": "Haugland",
                    "email": "tormod.haugland@gmail.com",
                }
            },
            context=Dict(user=user),
        )

        self.assertIsNone(result.errors)
        data = Dict(result.data)
        self.assertEqual("Tormod", data.patchUser.user.firstName)
        self.assertEqual("Haugland", data.patchUser.user.lastName)
        self.assertEqual("tormod.haugland@gmail.com", data.patchUser.user.email)

        result = schema.execute(
            mutation,
            variables={
                "id": to_global_id("UserNode", user.id),
                "input": {
                    "username": "tormod",
                    "firstName": "Tormod",
                    "lastName": "Haugland",
                    "email": "tormod.haugland@gmail.com",
                }
            },
            context=Dict(user=user_two),
        )

        self.assertIsNotNone(result.errors)
