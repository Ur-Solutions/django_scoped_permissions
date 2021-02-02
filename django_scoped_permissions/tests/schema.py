import graphene
from graphene import Node
from graphene_django import DjangoObjectType, DjangoConnectionField
from graphql import GraphQLError

from django_scoped_permissions.core import create_scope
from django_scoped_permissions.graphql import (
    ScopedDjangoCreateMutation,
    ScopedDjangoPatchMutation,
    ScopedDjangoUpdateMutation,
    ScopedDjangoDeleteMutation,
)
from django_scoped_permissions.tests.models import Pet, User


class PetNode(DjangoObjectType):
    class Meta:
        model = Pet
        interfaces = (Node,)

    @classmethod
    def get_node(self, info, id):
        return Pet.objects.get(pk=id)


class UserNode(DjangoObjectType):
    class Meta:
        model = User
        interfaces = (Node,)


class PetQuery(graphene.ObjectType):

    user = Node.Field(UserNode)

    pet = Node.Field(PetNode)
    all_pets = DjangoConnectionField(PetNode)

    def resolve_all_pets(self, info, *args, **kwargs):
        user = info.context.user
        company = info.context.company
        return Pet.objects.all()


class CreatePetMutation(ScopedDjangoCreateMutation):
    class Meta:
        model = Pet

        permissions = [
            create_scope(Pet, "create"),
            create_scope(User, "edit"),
        ]


class PatchPetMutation(ScopedDjangoPatchMutation):
    class Meta:
        model = Pet


class UpdatePetMutation(ScopedDjangoUpdateMutation):
    class Meta:
        model = Pet


class DeletePetMutation(ScopedDjangoDeleteMutation):
    class Meta:
        model = Pet


class CreateUserMutation(ScopedDjangoCreateMutation):
    class Meta:
        model = User


class PetMutations(graphene.ObjectType):
    create_pet = CreatePetMutation.Field()
    update_pet = UpdatePetMutation.Field()
    patch_pet = PatchPetMutation.Field()
    delete_pet = DeletePetMutation.Field()

    create_user = CreateUserMutation.Field()


class Query(PetQuery):
    pass


class CreateUserMutation(ScopedDjangoCreateMutation):
    class Meta:
        model = User
        optional_fields = ("password", "username")
        required_fields = ("primary_organization",)
        permissions = [
            create_scope(User, "create"),
        ]

    @classmethod
    def before_save(cls, root, info, input, obj):
        raise GraphQLError("Epic fail")
        obj.username = obj.email


class Mutation(graphene.ObjectType):
    create_user = CreateUserMutation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation,)
