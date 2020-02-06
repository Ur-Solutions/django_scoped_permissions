import graphene
from graphene import Node
from graphene_django import DjangoObjectType, DjangoConnectionField
from graphene_django_cud.mutations import (
    DjangoCreateMutation,
    DjangoPatchMutation,
    DjangoUpdateMutation,
    DjangoDeleteMutation,
)

from users.models import User, UserType

#################################
# Nodes
#################################


class UserNode(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (Node,)

    @classmethod
    def get_node(cls, info, id):
        print(vars(info.context))
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
    user = Node.Field(UserNode)
    all_users = DjangoConnectionField(UserNode)

    def resolve_all_users(self, info, *args, **kwargs):
        return User.objects.filter(companies=info.context.company)

    user_type = Node.Field(UserTypeNode)
    all_user_types = DjangoConnectionField(UserTypeNode)

    def resolve_all_user_types(self, info, *args, **kwargs):
        return UserTypes.objects.filter(company=info.context.company)


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


class UserMutations(graphene.ObjectType):
    create_user = CreateUserMutation.Field()
    update_user = UpdateUserMutation.Field()
    patch_user = PatchUserMutation.Field()
    delete_user = DeleteUserMutation.Field()
