from graphql import GraphQLError
from graphene_django_cud.util import disambiguate_id
from graphene_django_cud.mutations import (
    DjangoCreateMutation,
    DjangoPatchMutation,
    DjangoUpdateMutation,
    DjangoDeleteMutation,
)


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
