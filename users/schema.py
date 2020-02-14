from graphql import GraphQLError
import graphene
from graphene import Node
from graphene_django import DjangoObjectType, DjangoConnectionField
from graphene_django_cud.mutations import (
    DjangoCreateMutation,
    DjangoPatchMutation,
    DjangoUpdateMutation,
    DjangoDeleteMutation,
)
from graphene_django_cud.util import disambiguate_id
from django.core.exceptions import PermissionDenied

from permissions.models import ScopedPermission
from users.models import User, UserType

#################################
# Nodes
#################################


class UserNode(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (Node,)

    scopes = graphene.List(graphene.String)

    def resolve_scopes(self: User, info, *args, **kwargs):
        return self.get_scopes()

    @classmethod
    def get_node(cls, info, id):
        return User.objects.get(pk=id)


class UserTypeNode(DjangoObjectType):
    class Meta:
        model = UserType
        interfaces = (Node,)

    @classmethod
    def get_node(cls, info, id):
        return UserType.objects.get(pk=id)


#################################
# Query
#################################


class UserQuery(graphene.ObjectType):
    me = graphene.Field(UserNode)
    user = Node.Field(UserNode)
    all_users = DjangoConnectionField(UserNode)

    def resolve_me(self, info, *args, **kwargs):
        return info.context.user

    def resolve_all_users(self, info, *args, **kwargs):
        return User.objects.filter(companies=info.context.company)

    user_type = Node.Field(UserTypeNode)
    all_user_types = DjangoConnectionField(UserTypeNode)

    def resolve_all_user_types(self, info, *args, **kwargs):
        return UserType.objects.filter(company=info.context.company)


#################################
# Mutations
#################################


class CreateUserMutation(DjangoCreateMutation):
    class Meta:
        model = User
        exclude_fields = ("created_at", "updated_at", "has_registered", "password")


class UpdateUserMutation(DjangoUpdateMutation):
    class Meta:
        model = User
        exclude_fields = ("created_at", "updated_at", "has_registered", "password")


class PatchUserMutation(DjangoPatchMutation):
    class Meta:
        model = User
        exclude_fields = ("created_at", "updated_at", "has_registered", "password")


class DeleteUserMutation(DjangoDeleteMutation):
    class Meta:
        model = User


class CreateUserTypeMutation(DjangoCreateMutation):
    class Meta:
        model = UserType


class UpdateUserTypeMutation(DjangoUpdateMutation):
    class Meta:
        model = UserType


class PatchUserTypeMutation(DjangoPatchMutation):
    class Meta:
        model = UserType


class DeleteUserTypeMutation(DjangoDeleteMutation):
    class Meta:
        model = UserType


class ToggleScopedPermissionMutation(graphene.Mutation):
    class Arguments:
        user_type = graphene.ID(required=True)
        scope = graphene.String(required=True)
        exclude = graphene.Boolean(required=False)
        remove = graphene.Boolean(required=False)

    user_type = graphene.Field(UserTypeNode)

    def mutate(self, info, user_type, scope, exclude=None, remove=False):
        try:
            user_type = UserType.objects.get(pk=disambiguate_id(user_type))
        except UserType.DoesNotExist:
            raise GraphQLError("UserType does not exist")

        user = info.context.user
        if not user_type.has_permission(user, "update"):
            raise PermissionDenied("You do not have permission to do this")

        if remove:
            try:
                if exclude is None:
                    permission = user_type.scoped_permissions.get(scope=scope)
                else:
                    permission = user_type.scoped_permissions.get(
                        scope=scope, exclude=exclude
                    )
                user_type.scoped_permissions.remove(permission)
            except ScopedPermission.DoesNotExist:
                pass
        else:
            if exclude is None:
                exclude = False

            # First, remove any existing permissions with same scope from user type
            existing_permissions = user_type.scoped_permissions.filter(scope=scope)
            if existing_permissions.exists():
                user_type.scoped_permissions.remove(*existing_permissions)

            # Then, get or create a new permission, and add it to user_type
            permission, _ = ScopedPermission.objects.get_or_create(
                scope=scope, exclude=exclude
            )
            user_type.scoped_permissions.add(permission)

        return ToggleScopedPermissionMutation(user_type=user_type)


class UserMutations(graphene.ObjectType):
    create_user = CreateUserMutation.Field()
    update_user = UpdateUserMutation.Field()
    patch_user = PatchUserMutation.Field()
    delete_user = DeleteUserMutation.Field()

    create_user_type = CreateUserTypeMutation.Field()
    update_user_type = UpdateUserTypeMutation.Field()
    patch_user_type = PatchUserTypeMutation.Field()
    delete_user_type = DeleteUserTypeMutation.Field()

    toggle_scoped_permission = ToggleScopedPermissionMutation.Field()
