from typing import Tuple, Mapping, Union, Iterable

from graphene import Node
from graphene_django import DjangoObjectType
from graphene_django.types import DjangoObjectTypeOptions
from graphene_django_cud.mutations import DjangoPatchMutation, DjangoDeleteMutation, DjangoBatchCreateMutation, \
    DjangoBatchDeleteMutation, DjangoFilterDeleteMutation
from graphene_django_cud.mutations.create import DjangoCreateMutation
from graphene_django_cud.mutations.delete import DjangoDeleteMutationOptions
from graphene_django_cud.mutations.patch import DjangoPatchMutationOptions
from graphene_django_cud.mutations.update import (
    DjangoUpdateMutationOptions,
    DjangoUpdateMutation,
)
from graphql import GraphQLError

from django_scoped_permissions.graphql_util import (
    expand_scopes_from_context,
    create_resolver_from_method,
    create_resolver_from_scopes,
)
from django_scoped_permissions.models import HasScopedPermissionsMixin, ScopedModelMixin


class ScopedDjangoNodeOptions(DjangoObjectTypeOptions):
    allow_anonymous = False  # type: bool
    node_permissions = None  # type: Tuple[str]
    field_permissions = None  # type: Mapping[str, Union[bool, Tuple[str]]]


class ScopedDjangoNode(DjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        node_permissions=None,
        field_permissions=None,
        allow_anonymous=False,
        _meta=None,
        **options,
    ):
        if not _meta:
            _meta = ScopedDjangoNodeOptions(cls)

        _meta.allow_anonymous = allow_anonymous
        _meta.node_permissions = node_permissions
        _meta.field_permissions = field_permissions
        interfaces = options.get("interfaces", ()) + (Node,)

        super().__init_subclass_with_meta__(
            _meta=_meta, interfaces=interfaces, **options
        )

        # Great, the class is set up. Now let's add permission guards.
        node_permissions = node_permissions or {}
        field_permissions = field_permissions or {}

        for field, permissions in field_permissions.items():
            if callable(permissions):
                if hasattr(cls, f"resolve_{field}"):
                    continue

                setattr(
                    cls,
                    f"resolve_{field}",
                    create_resolver_from_method(field, permissions),
                )
            elif isinstance(permissions, tuple) or isinstance(permissions, list):
                if hasattr(cls, f"resolve_{field}"):
                    continue

                setattr(
                    cls,
                    f"resolve_{field}",
                    create_resolver_from_scopes(field, permissions),
                )
            elif isinstance(permissions, str):
                if hasattr(cls, f"resolve_{field}"):
                    continue

                setattr(
                    cls,
                    f"resolve_{field}",
                    create_resolver_from_scopes(field, [permissions]),
                )
            else:
                raise ValueError(
                    f"Invalid field type {type(permissions)} given to ScopedDjangoNode for field {field}"
                )

    @classmethod
    def get_node(cls, info, id):
        user = info.context.user
        if not cls._meta.allow_anonymous and user.is_anonymous:
            raise GraphQLError("You are not permitted to view this.")

        if cls._meta.node_permissions:
            if not user.has_scoped_permissions(*cls._meta.node_permissions):
                raise GraphQLError("You are not permitted to view this.")
        else:
            # Try to get object and see if we can get the required scopes from it
            obj = cls._meta.model.objects.get(pk=id)
            if hasattr(obj, "get_base_scopes"):
                if not user.has_scoped_permissions(*obj.get_base_scopes()):
                    raise GraphQLError("You are not permitted to view this.")

        return super().get_node(info, id)


class ScopedDjangoCreateMutation(DjangoCreateMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = cls.get_permissions(root, info, input) or []

        if not hasattr(permissions, '__len__') or len(permissions) == 0:
            return

        context = {"context": info.context, "input": input}

        expanded_permissions = expand_scopes_from_context(permissions, context)

        if not isinstance(info.context.user, HasScopedPermissionsMixin):
            raise GraphQLError("You are not permitted to view this.")

        if not info.context.user.has_scoped_permissions(*expanded_permissions):
            raise GraphQLError("You are not permitted to view this.")

class ScopedDjangoBatchCreateMutation(DjangoBatchCreateMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = cls.get_permissions(root, info, input) or []

        if not hasattr(permissions, '__len__') or len(permissions) == 0:
            return

        context = {"context": info.context, "input": input}

        expanded_permissions = expand_scopes_from_context(permissions, context)

        if not isinstance(info.context.user, HasScopedPermissionsMixin):
            raise GraphQLError("You are not permitted to view this.")

        if not info.context.user.has_scoped_permissions(*expanded_permissions):
            raise GraphQLError("You are not permitted to view this.")


class ScopedDjangoPatchMutationOptions(DjangoPatchMutationOptions):
    permission_action = "update"  # type: str


class ScopedDjangoPatchMutation(DjangoPatchMutation):
    class Meta:
        abstract = True

    @classmethod
    def get_permissions(cls, root, info, input, id, obj) -> Iterable[str]:
        super_permissions = super().get_permissions(root, info, input, id, obj) or []

        if hasattr(super_permissions, '__len__') and len(super_permissions) > 0:
            return super_permissions

        # If we don't have explicit permissions we use some defaults here.
        if cls._meta.permission_action == "":
            return ["{base_scopes}"]
        else:
            return [
                # Double curly brackets escapes them
                f"{{base_scopes}}:{cls._meta.permission_action}"
            ]

    @classmethod
    def check_permissions(cls, root, info, input, id, obj) -> None:
        permissions = cls.get_permissions(root, info, input, id, obj)

        context = {}

        if isinstance(obj, ScopedModelMixin):
            context["base_scopes"] = obj.get_base_scopes()

        context["context"] = info.context
        context["input"] = input
        context["id"] = id
        context["obj"] = obj

        expanded_permissions = expand_scopes_from_context(permissions, context)

        if not isinstance(info.context.user, HasScopedPermissionsMixin):
            raise GraphQLError("You are not permitted to view this.")

        if not info.context.user.has_scoped_permissions(*expanded_permissions):
            raise GraphQLError("You are not permitted to view this.")

    @classmethod
    def __init_subclass_with_meta__(
        cls, _meta=None, permission_action="update", **options
    ):
        if _meta is None:
            _meta = ScopedDjangoPatchMutationOptions(cls)

        _meta.permission_action = permission_action

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoUpdateMutationOptions(DjangoUpdateMutationOptions):
    permission_action = "update"  # type: str


class ScopedDjangoUpdateMutation(DjangoUpdateMutation):
    class Meta:
        abstract = True

    @classmethod
    def get_permissions(cls, root, info, input, id, obj) -> Iterable[str]:
        super_permissions = super().get_permissions(root, info, input, id, obj) or []

        if hasattr(super_permissions, '__len__') and len(super_permissions) > 0:
            return super_permissions

        # If we don't have explicit permissions we use some defaults here.
        if cls._meta.permission_action == "":
            return ["{base_scopes}"]
        else:
            return [
                # Double curly brackets escapes them
                f"{{base_scopes}}:{cls._meta.permission_action}"
            ]

    @classmethod
    def check_permissions(cls, root, info, input, id, obj) -> None:
        permissions = cls.get_permissions(root, info, input, id, obj) or []

        context = {}

        if isinstance(obj, ScopedModelMixin):
            context["base_scopes"] = obj.get_base_scopes()

        context["context"] = info.context
        context["input"] = input
        context["id"] = id
        context["obj"] = obj

        expanded_permissions = expand_scopes_from_context(permissions, context)

        if not isinstance(info.context.user, HasScopedPermissionsMixin):
            raise GraphQLError("You are not permitted to view this.")

        if not info.context.user.has_scoped_permissions(*expanded_permissions):
            raise GraphQLError("You are not permitted to view this.")

    @classmethod
    def __init_subclass_with_meta__(
        cls, _meta=None, permission_action="update", **options
    ):
        if _meta is None:
            _meta = ScopedDjangoUpdateMutationOptions(cls)

        _meta.permission_action = permission_action

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoDeleteMutationOptions(DjangoDeleteMutationOptions):
    permission_action = "delete"  # type: str


class ScopedDjangoDeleteMutation(DjangoDeleteMutation):
    class Meta:
        abstract = True

    @classmethod
    def get_permissions(cls, root, info, id, obj) -> Iterable[str]:
        super_permissions = super().get_permissions(root, info, id, obj)

        if hasattr(super_permissions, '__len__') and len(super_permissions) > 0:
            return super_permissions

        # If we don't have explicit permissions we use some defaults here.
        if cls._meta.permission_action == "":
            return ["{base_scopes}"]
        else:
            return [
                # Double curly brackets escapes them
                f"{{base_scopes}}:{cls._meta.permission_action}"
            ]

    @classmethod
    def check_permissions(cls, root, info, id, obj) -> None:
        permissions = cls.get_permissions(root, info,  id, obj) or []

        context = {}

        if isinstance(obj, ScopedModelMixin):
            context["base_scopes"] = obj.get_base_scopes()

        context["context"] = info.context
        context["input"] = input
        context["id"] = id
        context["obj"] = obj

        expanded_permissions = expand_scopes_from_context(permissions, context)

        if not isinstance(info.context.user, HasScopedPermissionsMixin):
            raise GraphQLError("You are not permitted to view this.")

        if not info.context.user.has_scoped_permissions(*expanded_permissions):
            raise GraphQLError("You are not permitted to view this.")

    @classmethod
    def __init_subclass_with_meta__(
        cls, _meta=None, permission_action="delete", **options
    ):
        if _meta is None:
            _meta = ScopedDjangoUpdateMutationOptions(cls)

        _meta.permission_action = permission_action

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoBatchDeleteMutation(DjangoBatchDeleteMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = cls.get_permissions(root, info, input) or []

        if not hasattr(permissions, '__len__') or len(permissions) == 0:
            return

        context = {"context": info.context, "input": input}

        expanded_permissions = expand_scopes_from_context(permissions, context)

        if not isinstance(info.context.user, HasScopedPermissionsMixin):
            raise GraphQLError("You are not permitted to view this.")

        if not info.context.user.has_scoped_permissions(*expanded_permissions):
            raise GraphQLError("You are not permitted to view this.")


class ScopedDjangoFilterDeleteMutation(DjangoFilterDeleteMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = cls.get_permissions(root, info, input) or []

        if not hasattr(permissions, '__len__') or len(permissions) == 0:
            return

        context = {"context": info.context, "input": input}

        expanded_permissions = expand_scopes_from_context(permissions, context)

        if not isinstance(info.context.user, HasScopedPermissionsMixin):
            raise GraphQLError("You are not permitted to view this.")

        if not info.context.user.has_scoped_permissions(*expanded_permissions):
            raise GraphQLError("You are not permitted to view this.")
