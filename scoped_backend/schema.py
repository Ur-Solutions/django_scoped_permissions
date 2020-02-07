import graphene

from permissions.schema import ScopedPermissionQuery
from users.schema import UserQuery, UserMutations
from pets.schema import PetQuery, PetMutations


class Query(
    ScopedPermissionQuery, UserQuery, PetQuery, graphene.ObjectType,
):
    pass


class Mutation(
    UserMutations, PetMutations, graphene.ObjectType,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
