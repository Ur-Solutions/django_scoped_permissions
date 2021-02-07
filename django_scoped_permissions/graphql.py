from typing import Tuple, Mapping, Union, Iterable, List

from graphene import Node
from graphene_django import DjangoObjectType
from graphene_django.types import DjangoObjectTypeOptions
from graphene_django_cud.mutations import (
    DjangoPatchMutation,
    DjangoDeleteMutation,
    DjangoBatchCreateMutation,
    DjangoBatchDeleteMutation,
    DjangoFilterDeleteMutation,
)
from graphene_django_cud.mutations.create import DjangoCreateMutation
from graphene_django_cud.mutations.delete import DjangoDeleteMutationOptions
from graphene_django_cud.mutations.patch import DjangoPatchMutationOptions
from graphene_django_cud.mutations.update import (
    DjangoUpdateMutationOptions,
    DjangoUpdateMutation,
)
from graphql import GraphQLError

from django_scoped_permissions.guards import ScopedPermissionGuard
from django_scoped_permissions.models import (
    ScopedModelMixin,
    ScopedPermissionHolderMixin,
)
from django_scoped_permissions.util import (
    create_resolver_from_method,
    create_resolver_from_scopes,
)


class ScopedDjangoNodeOptions(DjangoObjectTypeOptions):
    allow_anonymous = False  # type: bool
    node_permissions = None  # type: Tuple[str]
    field_permissions = None  # type: Mapping[str, Union[bool, Tuple[str]]]
    verb = "read"  # type: str


class ScopedDjangoNode(DjangoObjectType):
    class Meta:
        abstract = True

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        node_permissions=None,
        field_permissions=None,
        allow_anonymous=False,
        verb="read",
        _meta=None,
        **options,
    ):
        if not _meta:
            _meta = ScopedDjangoNodeOptions(cls)

        _meta.allow_anonymous = allow_anonymous
        _meta.node_permissions = node_permissions
        _meta.field_permissions = field_permissions
        _meta.verb = verb
        interfaces = options.get("interfaces", ()) + (Node,)

        # Great, the class is set up. Now let's add permission guards.
        field_permissions = field_permissions or {}

        permission_guard = ScopedPermissionGuard(node_permissions)
        _meta.permission_guard = permission_guard

        super().__init_subclass_with_meta__(
            _meta=_meta, interfaces=interfaces, **options
        )

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
        if not cls._meta.allow_anonymous and not isinstance(
            user, ScopedPermissionHolderMixin
        ):
            raise GraphQLError("You are not permitted to view this.")

        granting_permissions = (
            user.get_granting_scopes() if hasattr(user, "get_granting_scopes") else []
        )

        Model = cls._meta.model
        obj = Model.objects.get(pk=id)

        context = {
            "user": user,
            "context": info.context,
            # Deprecated
            "obj": obj,
        }

        if isinstance(obj, ScopedModelMixin):
            context["base_scopes"] = obj.get_base_scopes()
            context["required_scopes"] = obj.get_required_scopes()

        # If we have explicit permission, we check against the guard
        if cls._meta.node_permissions:
            if not cls._meta.permission_guard.has_permission(
                granting_permissions, context
            ):
                raise GraphQLError("You are not permitted to view this.")
        elif isinstance(obj, ScopedModelMixin):
            if not isinstance(user, ScopedPermissionHolderMixin):
                raise GraphQLError("You are not permitted to view this.")

            if not obj.can_be_accessed_by(user, cls._meta.verb):
                raise GraphQLError("You are not permitted to view this.")

        return super().get_node(info, id)


class ScopedDjangoCreateMutation(DjangoCreateMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = cls.get_permissions(root, info, input) or []

        user = info.context.user

        permission_guard = ScopedPermissionGuard(permissions)
        context = {"context": info.context, "input": input, "user": info.context.user}

        granting_permissions = (
            user.get_granting_scopes() if hasattr(user, "get_granting_scopes") else []
        )

        if not permission_guard.has_permission(granting_permissions):
            raise GraphQLError("You are not permitted to view this.")


class ScopedDjangoBatchCreateMutation(DjangoBatchCreateMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = cls.get_permissions(root, info, input) or []

        if not hasattr(permissions, "__len__") or len(permissions) == 0:
            return

        user = info.context.user

        permission_guard = ScopedPermissionGuard(permissions)
        context = {"context": info.context, "input": input, "user": info.context.user}

        granting_permissions = (
            user.get_granting_scopes() if hasattr(user, "get_granting_scopes") else []
        )

        if not permission_guard.has_permission(granting_permissions, context=context):
            raise GraphQLError("You are not permitted to view this.")


class ScopedDjangoPatchMutationOptions(DjangoPatchMutationOptions):
    verb = "update"  # type: str


class ScopedDjangoPatchMutation(DjangoPatchMutation):
    class Meta:
        abstract = True

    @classmethod
    def get_permissions(
        cls, root, info, input, id, obj
    ) -> Union[Iterable[str], ScopedPermissionGuard]:
        super_permissions = super().get_permissions(root, info, input, id, obj) or []

        if (
            hasattr(super_permissions, "__len__")
            and len(super_permissions) > 0
            or isinstance(super_permissions, ScopedPermissionGuard)
        ):
            return super_permissions

        # If we don't have explicit permissions we use some defaults here.
        return ScopedPermissionGuard(scope="{required_scopes}", verb=cls._meta.verb)

    @classmethod
    def check_permissions(cls, root, info, input, id, obj) -> None:
        permissions = cls.get_permissions(root, info, input, id, obj) or []

        if not hasattr(permissions, "__len__") or len(permissions) == 0:
            return

        user = info.context.user

        permission_guard = ScopedPermissionGuard(permissions)
        context = {}

        if isinstance(obj, ScopedModelMixin):
            context["base_scopes"] = obj.get_base_scopes()
            context["required_scopes"] = obj.get_required_scopes()

        granting_permissions = (
            user.get_granting_scopes() if hasattr(user, "get_granting_scopes") else []
        )

        context["context"] = info.context
        context["input"] = input
        context["id"] = id
        context["obj"] = obj

        if not permission_guard.has_permission(granting_permissions, context=context):
            raise GraphQLError("You are not permitted to view this.")

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, verb="update", **options):
        if _meta is None:
            _meta = ScopedDjangoPatchMutationOptions(cls)

        _meta.verb = verb

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoUpdateMutationOptions(DjangoUpdateMutationOptions):
    verb = "update"  # type: str


class ScopedDjangoUpdateMutation(DjangoUpdateMutation):
    class Meta:
        abstract = True

    @classmethod
    def get_permissions(
        cls, root, info, input, id, obj
    ) -> Union[Iterable[str], ScopedPermissionGuard]:
        super_permissions = super().get_permissions(root, info, input, id, obj) or []

        if (
            hasattr(super_permissions, "__len__")
            and len(super_permissions) > 0
            or isinstance(super_permissions, ScopedPermissionGuard)
        ):
            return super_permissions

        # If we don't have explicit permissions we use some defaults here.
        return ScopedPermissionGuard(scope="{required_scopes}", verb=cls._meta.verb)

    @classmethod
    def check_permissions(cls, root, info, input, id, obj) -> None:
        permissions = cls.get_permissions(root, info, input, id, obj) or []

        if not hasattr(permissions, "__len__") or len(permissions) == 0:
            return

        user = info.context.user

        permission_guard = ScopedPermissionGuard(permissions)
        context = {}

        if isinstance(obj, ScopedModelMixin):
            context["base_scopes"] = obj.get_base_scopes()
            context["required_scopes"] = obj.get_required_scopes()

        granting_permissions = (
            user.get_granting_scopes() if hasattr(user, "get_granting_scopes") else []
        )

        context["context"] = info.context
        context["input"] = input
        context["id"] = id
        context["obj"] = obj

        if not permission_guard.has_permission(granting_permissions, context=context):
            raise GraphQLError("You are not permitted to view this.")

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, verb="update", **options):
        if _meta is None:
            _meta = ScopedDjangoUpdateMutationOptions(cls)

        _meta.verb = verb

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoDeleteMutationOptions(DjangoDeleteMutationOptions):
    verb = "delete"  # type: str


class ScopedDjangoDeleteMutation(DjangoDeleteMutation):
    class Meta:
        abstract = True

    @classmethod
    def get_permissions(
        cls, root, info, id, obj
    ) -> Union[Iterable[str], ScopedPermissionGuard]:
        super_permissions = super().get_permissions(root, info, id, obj) or []

        if (
            hasattr(super_permissions, "__len__")
            and len(super_permissions) > 0
            or isinstance(super_permissions, ScopedPermissionGuard)
        ):
            return super_permissions

        return ScopedPermissionGuard(scope="{required_scopes}", verb=cls._meta.verb)

    @classmethod
    def check_permissions(cls, root, info, id, obj) -> None:
        permissions = cls.get_permissions(root, info, id, obj) or []

        if not hasattr(permissions, "__len__") or len(permissions) == 0:
            return

        user = info.context.user

        permission_guard = ScopedPermissionGuard(permissions)
        context = {}

        if isinstance(obj, ScopedModelMixin):
            context["base_scopes"] = obj.get_base_scopes()
            context["required_scopes"] = obj.get_required_scopes()

        granting_permissions = (
            user.get_granting_scopes() if hasattr(user, "get_granting_scopes") else []
        )

        context["context"] = info.context
        context["id"] = id
        context["obj"] = obj

        if not permission_guard.has_permission(granting_permissions, context=context):
            raise GraphQLError("You are not permitted to view this.")

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, verb="delete", **options):
        if _meta is None:
            _meta = ScopedDjangoUpdateMutationOptions(cls)

        _meta.verb = verb

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoBatchDeleteMutation(DjangoBatchDeleteMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = cls.get_permissions(root, info, input) or []

        if not hasattr(permissions, "__len__") or len(permissions) == 0:
            return

        user = info.context.user

        permission_guard = ScopedPermissionGuard(permissions)
        context = {"context": info.context, "input": input, "user": info.context.user}

        granting_permissions = (
            user.get_granting_scopes() if hasattr(user, "get_granting_scopes") else []
        )

        if not permission_guard.has_permission(granting_permissions, context=context):
            raise GraphQLError("You are not permitted to view this.")


class ScopedDjangoFilterDeleteMutation(DjangoFilterDeleteMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = cls.get_permissions(root, info, input) or []

        if not hasattr(permissions, "__len__") or len(permissions) == 0:
            return

        user = info.context.user

        permission_guard = ScopedPermissionGuard(permissions)
        context = {"context": info.context, "input": input, "user": info.context.user}

        granting_permissions = (
            user.get_granting_scopes() if hasattr(user, "get_granting_scopes") else []
        )

        if not permission_guard.has_permission(granting_permissions, context=context):
            raise GraphQLError("You are not permitted to view this.")
