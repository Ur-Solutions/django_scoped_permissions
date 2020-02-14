import graphene
from graphene_django import DjangoObjectType
from graphql import GraphQLError
from graphene_django_cud.util import disambiguate_id
from graphene_django_cud.mutations import (
    DjangoCreateMutation,
    DjangoBatchCreateMutation,
    DjangoPatchMutation,
    DjangoUpdateMutation,
    DjangoDeleteMutation,
)


class ScopedDjangoCreateMutation(DjangoCreateMutation):
    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user
        model = cls._meta.model
        model_name = model._meta.model_name
        if not user.has_create_permission(model_name, "create"):
            fail_message = getattr(
                cls._meta,
                "fail_message",
                "You do not have permission to create this object",
            )
            raise GraphQLError(fail_message)

        return super().mutate(root, info, input)


class ScopedDjangoBatchCreateMutation(DjangoBatchCreateMutation):
    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info, input):
        user = info.context.user
        model = cls._meta.model
        model_name = model._meta.model_name
        if not user.has_create_permission(model_name, "create"):
            fail_message = getattr(
                cls._meta,
                "fail_message",
                "You do not have permission to create these objects",
            )
            raise GraphQLError(fail_message)

        return super().mutate(root, info, input)


class ScopedDjangoPatchMutation(DjangoPatchMutation):
    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info, id, input):
        user = info.context.user
        model = cls._meta.model
        obj = model.objects.get(pk=disambiguate_id(id))
        if not obj.has_permission(user, "update"):
            fail_message = getattr(
                cls._meta,
                "fail_message",
                "You do not have permission to update this object",
            )
            raise GraphQLError(fail_message)

        return super().mutate(root, info, id, input)


class ScopedDjangoUpdateMutation(DjangoUpdateMutation):
    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info, id, input):
        user = info.context.user
        model = cls._meta.model
        obj = model.objects.get(pk=disambiguate_id(id))
        if not obj.has_permission(user, "update"):
            fail_message = getattr(
                cls._meta,
                "fail_message",
                "You do not have permission to update this object",
            )
            raise GraphQLError(fail_message)

        return super().mutate(root, info, id, input)


class ScopedDjangoDeleteMutation(DjangoDeleteMutation):
    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info, id):
        user = info.context.user
        model = cls._meta.model
        obj = model.objects.get(pk=disambiguate_id(id))
        if not obj.has_permission(user, "delete"):
            fail_message = getattr(
                cls._meta,
                "fail_message",
                "You do not have permission to delete this object",
            )
            raise GraphQLError(fail_message)

        return super().mutate(root, info, id)


class ScopedModelNode(DjangoObjectType):
    class Meta:
        abstract = True

    base_scopes = graphene.List(graphene.String)

    def resolve_base_scopes(self, info, **kwargs):
        return self.get_base_scopes()
