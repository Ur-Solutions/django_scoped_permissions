import graphene

from permissions.schema import ScopedPermissionQuery
from users.schema import UserQuery, UserMutations


class Query(
    ScopedPermissionQuery, UserQuery, graphene.ObjectType,
):
    pass


class Mutation(
    UserMutations, graphene.ObjectType,
):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
