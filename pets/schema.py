import graphene
from graphene import Node
from graphene_django import DjangoObjectType, DjangoConnectionField
from graphene_django_cud.mutations import (
    DjangoCreateMutation,
    DjangoPatchMutation,
    DjangoUpdateMutation,
    DjangoDeleteMutation,
)
from permissions.scoped_mutations import (
    ScopedDjangoCreateMutation,
    ScopedDjangoPatchMutation,
    ScopedDjangoUpdateMutation,
    ScopedDjangoDeleteMutation,
)

from pets.models import Pet


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
        return Pet.objects.all()


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
