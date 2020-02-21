import graphene
from graphene import Node
from graphene_django import DjangoObjectType, DjangoConnectionField

from django_scoped_permissions.models import ScopedPermission


class ScopedPermissionNode(DjangoObjectType):
    class Meta:
        model = ScopedPermission
        interfaces = (Node,)

    @classmethod
    def get_node(self, info, id):
        return ScopedPermission.objects.get(pk=id)


class ScopedPermissionQuery(graphene.ObjectType):
    scoped_permission = Node.Field(ScopedPermissionNode)
    all_scoped_permissions = DjangoConnectionField(ScopedPermissionNode)

    def resolve_all_scoped_permissions(self, info, *args, **kwargs):
        return ScopedPermission.objects.all()
