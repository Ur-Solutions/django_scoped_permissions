import graphene
import pytest
from addict import Dict
from graphene_django import DjangoObjectType
from graphql_relay import to_global_id

from django_scoped_permissions.graphql import (
    ScopedDjangoBatchPatchMutation,
    ScopedDjangoBatchUpdateMutation,
    ScopedDjangoFilterUpdateMutation,
)
from django_scoped_permissions.tests.factories import PetFactory, UserFactory
from django_scoped_permissions.tests.models import Pet


class BulkPetNode(DjangoObjectType):
    class Meta:
        model = Pet
        fields = ("id", "name", "age")
        interfaces = (graphene.Node,)


class BatchPatchPet(ScopedDjangoBatchPatchMutation):
    class Meta:
        model = Pet
        fields = ("id", "name", "age")
        permissions = ("pet:bulk-update",)


class BatchUpdatePet(ScopedDjangoBatchUpdateMutation):
    class Meta:
        model = Pet
        fields = ("id", "name", "age")
        permissions = ("pet:bulk-update",)


class FilterUpdatePet(ScopedDjangoFilterUpdateMutation):
    class Meta:
        model = Pet
        fields = ("name",)
        filter_fields = ("name",)
        permissions = ("pet:bulk-update",)


class Query(graphene.ObjectType):
    pet = graphene.Node.Field(BulkPetNode)


class Mutation(graphene.ObjectType):
    batch_patch = BatchPatchPet.Field()
    batch_update = BatchUpdatePet.Field()
    filter_update = FilterUpdatePet.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)


@pytest.mark.django_db
@pytest.mark.parametrize("operation", ["batchPatch", "batchUpdate", "filterUpdate"])
def test_bulk_mutations_require_permission_before_changing_rows(operation):
    actor = UserFactory()
    pets = PetFactory.create_batch(2, name="Before")
    untouched = PetFactory(name="Other")
    if operation == "filterUpdate":
        mutation = '''mutation {
            filterUpdate(filter: {name: "Before"}, data: {name: "After"}) {
                updatedCount
            }
        }'''
    else:
        inputs = ", ".join(
            '{id: "%s", name: "After", age: 11}'
            % to_global_id("BulkPetNode", pet.pk)
            for pet in pets
        )
        mutation = f"mutation {{ {operation}(input: [{inputs}]) {{ pets {{ name }} }} }}"

    denied = schema.execute(mutation, context_value=Dict(user=actor))
    assert denied.errors
    assert "not permitted" in denied.errors[0].message
    for pet in pets:
        pet.refresh_from_db()
        assert pet.name == "Before"

    actor.add_or_create_permission("pet:bulk-update")
    allowed = schema.execute(mutation, context_value=Dict(user=actor))
    assert allowed.errors is None
    for pet in pets:
        pet.refresh_from_db()
        assert pet.name == "After"
    untouched.refresh_from_db()
    assert untouched.name == "Other"
