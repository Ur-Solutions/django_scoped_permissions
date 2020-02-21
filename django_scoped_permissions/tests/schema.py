import graphene
from graphene import Node
from graphene_django import DjangoObjectType, DjangoConnectionField
from permissions.graphql import (
    ScopedDjangoCreateMutation,
    ScopedDjangoPatchMutation,
    ScopedDjangoUpdateMutation,
    ScopedDjangoDeleteMutation,
)

from django_scoped_permissions.util import read_scoped
from django_scoped_permissions.tests.models import Pet


class PetNode(DjangoObjectType):
    class Meta:
        model = Pet
        interfaces = (Node,)

    @classmethod
    def get_node(self, info, id):
        return Pet.objects.get(pk=id)


class PetQuery(graphene.ObjectType):
    pet = Node.Field(PetNode)
    all_pets = DjangoConnectionField(PetNode)

    def resolve_all_pets(self, info, *args, **kwargs):
        user = info.context.user
        company = info.context.company
        return read_scoped(Pet.objects.all(), user, company, {"user": user})


class CreatePetMutation(ScopedDjangoCreateMutation):
    class Meta:
        model = Pet


class PatchPetMutation(ScopedDjangoPatchMutation):
    class Meta:
        model = Pet


class UpdatePetMutation(ScopedDjangoUpdateMutation):
    class Meta:
        model = Pet


class DeletePetMutation(ScopedDjangoDeleteMutation):
    class Meta:
        model = Pet



class PetMutations(graphene.ObjectType):
    create_pet = CreatePetMutation.Field()
    update_pet = UpdatePetMutation.Field()
    patch_pet = PatchPetMutation.Field()
    delete_pet = DeletePetMutation.Field()
