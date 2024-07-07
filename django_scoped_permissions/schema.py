import graphene
from graphene import Node
from graphene_django import DjangoObjectType, DjangoConnectionField

from django_scoped_permissions.models import StoredScopedPermission


class ScopedPermissionNode(DjangoObjectType):
    class Meta:
        model = StoredScopedPermission
        interfaces = (Node,)

    @classmethod
    def get_node(self, info, id):
        return StoredScopedPermission.objects.get(pk=id)


class ScopedPermissionQuery(graphene.ObjectType):
    scoped_permission = Node.Field(ScopedPermissionNode)
    all_scoped_permissions = DjangoConnectionField(ScopedPermissionNode)

    def resolve_all_scoped_permissions(self, info, *args, **kwargs):
        return StoredScopedPermission.objects.all()
