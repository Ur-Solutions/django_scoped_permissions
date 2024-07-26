from typing import Tuple, Mapping, Union

from graphene import Node
from graphene_django import DjangoObjectType
from graphene_django.types import DjangoObjectTypeOptions
from graphene_django_cud.mutations import (
    DjangoPatchMutation,
    DjangoDeleteMutation,
    DjangoBatchCreateMutation,
    DjangoBatchDeleteMutation,
    DjangoFilterDeleteMutation, DjangoBatchPatchMutation, DjangoBatchUpdateMutation, DjangoFilterUpdateMutation,
)
from graphene_django_cud.mutations.create import DjangoCreateMutation, DjangoCreateMutationOptions
from graphene_django_cud.mutations.delete import DjangoDeleteMutationOptions
from graphene_django_cud.mutations.patch import DjangoPatchMutationOptions
from graphene_django_cud.mutations.update import (
    DjangoUpdateMutationOptions,
    DjangoUpdateMutation,
)

from django_scoped_permissions.core.scoped_permission import ScopedPermission, sp
from django_scoped_permissions.guards import ScopedPermissionGuard
from django_scoped_permissions.models import (
    ProtectedModelMixin,
    ScopedPermissionProviderMixin,
)
from django_scoped_permissions.util import (
    create_resolver_from_method,
    create_resolver_from_scopes,
)
from graphql import GraphQLError


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
            elif isinstance(permissions, ScopedPermission):
                if hasattr(cls, f"resolve_{field}"):
                    continue

                setattr(
                    cls,
                    f"resolve_{field}",
                    create_resolver_from_scopes(field, permissions),
                )
            else:
                raise ValueError(
                    f"Invalid field type {type(permissions)} given to ScopedDjangoNode for field {field}"
                )

    @classmethod
    def get_node(cls, info, id):
        user = info.context.user
        if not cls._meta.allow_anonymous and not isinstance(
                user, ScopedPermissionProviderMixin
        ):
            raise GraphQLError("You are not permitted to view this.")

        context = {
            "request": info.context,
            "context": info.context,
            "user": user,
            "id": id
        }

        granting_permissions = (
            user.get_granting_permissions(context) if hasattr(user, "get_granting_permissions") else []
        )

        Model = cls._meta.model
        queryset = Model.objects.all()
        obj = cls.get_queryset(queryset, info).get(pk=id)

        required_permissions = [sp(permission) for permission in cls._meta.node_permissions]

        if isinstance(obj, ProtectedModelMixin):
            obj_required_permissions = obj.get_required_permissions(context)
            required_permissions += obj_required_permissions

        if not any(
                required_permission.check_access(granting_permissions) for required_permission in required_permissions):
            raise GraphQLError("You are not permitted to view this.")

        return super().get_node(info, id)


def check_standard_create_or_batch_mutation_permissions(class_required_permissions, info, verb, input):
    user = info.context.user
    context = {
        **(input or {}),
        "context": info.context,
        "request": info.context,
        "input": input,
        "verb": verb
    }

    granting_permissions = (
        user.get_granting_permissions(context) if hasattr(user, "get_granting_permissions") else []
    )

    required_permissions = [permission.apply_context(context) for permission in class_required_permissions]

    if not any(
            required_permission.check_access(granting_permissions) for required_permission in required_permissions):
        raise GraphQLError("You are not permitted to view this.")


def check_standard_single_object_mutation_permissions(class_required_permissions, info, verb, input, id, obj):
    user = info.context.user
    context = {
        **(input or {}),
        "context": info.context,
        "request": info.context,
        "id": id,
        "input": input,
        "obj": obj,
        "verb": verb
    }

    obj_required_permissions = obj.get_required_permissions(context) if hasattr(obj,
                                                                                "get_required_permissions") else []
    required_permissions = [permission.apply_context(context) for permission in
                            class_required_permissions + obj_required_permissions]

    granting_permissions = (
        user.get_granting_permissions(context) if hasattr(user, "get_granting_permissions") else []
    )

    if not any(
            required_permission.check_access(granting_permissions) for required_permission in required_permissions):
        raise GraphQLError("You are not permitted to view this.")


class ScopedDjangoCreateMutationOptions(DjangoCreateMutationOptions):
    verb = "create"  # type: str


class ScopedDjangoCreateMutation(DjangoCreateMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = [sp(permission) for permission in cls.get_permissions(root, info, input) or []]
        return check_standard_create_or_batch_mutation_permissions(permissions, info, cls._meta.verb, input)

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, verb="update", **options):
        if _meta is None:
            _meta = ScopedDjangoCreateMutationOptions(cls)

        _meta.verb = verb

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoBatchCreateMutation(DjangoBatchCreateMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = [sp(permission) for permission in cls.get_permissions(root, info, input) or []]
        return check_standard_create_or_batch_mutation_permissions(permissions, info, cls._meta.verb, input)


class ScopedDjangoPatchMutationOptions(DjangoPatchMutationOptions):
    verb = "update"  # type: str


class ScopedDjangoPatchMutation(DjangoPatchMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input, id, obj) -> None:
        required_permissions = [sp(permission) for permission in cls.get_permissions(root, info, input, id, obj) or []]
        return check_standard_single_object_mutation_permissions(required_permissions, info, cls._meta.verb, input, id,
                                                                 obj)

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, verb="update", **options):
        if _meta is None:
            _meta = ScopedDjangoPatchMutationOptions(cls)

        _meta.verb = verb

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoBatchPatchMutationOptions(DjangoPatchMutationOptions):
    verb = "update"  # type: str


class ScopedDjangoBatchPatchMutation(DjangoBatchPatchMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = [sp(permission) for permission in cls.get_permissions(root, info, input) or []]
        return check_standard_create_or_batch_mutation_permissions(permissions, info, cls._meta.verb, input)

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, verb="update", **options):
        if _meta is None:
            _meta = ScopedDjangoBatchPatchMutationOptions(cls)

        _meta.verb = verb

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoUpdateMutationOptions(DjangoUpdateMutationOptions):
    verb = "update"  # type: str


class ScopedDjangoUpdateMutation(DjangoUpdateMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input, id, obj) -> None:
        required_permissions = [sp(permission) for permission in cls.get_permissions(root, info, input, id, obj) or []]
        return check_standard_single_object_mutation_permissions(required_permissions, info, cls._meta.verb, input, id,
                                                                 obj)

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, verb="update", **options):
        if _meta is None:
            _meta = ScopedDjangoUpdateMutationOptions(cls)

        _meta.verb = verb

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoBatchUpdateMutationOptions(DjangoUpdateMutationOptions):
    verb = "update"  # type: str


class ScopedDjangoBatchUpdateMutation(DjangoBatchUpdateMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = [sp(permission) for permission in cls.get_permissions(root, info, input) or []]
        return check_standard_create_or_batch_mutation_permissions(permissions, info, cls._meta.verb, input)

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, verb="update", **options):
        if _meta is None:
            _meta = ScopedDjangoBatchUpdateMutationOptions(cls)

        _meta.verb = verb

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoFilterUpdateMutationOptions(DjangoUpdateMutationOptions):
    verb = "update"  # type: str


class ScopedDjangoFilterUpdateMutation(DjangoFilterUpdateMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, filter, data) -> None:
        permissions = [sp(permission) for permission in cls.get_permissions(root, info, filter, data) or []]
        return check_standard_create_or_batch_mutation_permissions(permissions, info, cls._meta.verb, input)

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, verb="update", **options):
        if _meta is None:
            _meta = ScopedDjangoFilterUpdateMutationOptions(cls)

        _meta.verb = verb

        return super().__init_subclass_with_meta__(_meta=_meta, **options)


class ScopedDjangoDeleteMutationOptions(DjangoDeleteMutationOptions):
    verb = "delete"  # type: str


class ScopedDjangoDeleteMutation(DjangoDeleteMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, id, obj) -> None:
        required_permissions = [sp(permission) for permission in cls.get_permissions(root, info, id, obj) or []]
        return check_standard_single_object_mutation_permissions(required_permissions, info, cls._meta.verb, {}, id,
                                                                 obj)

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
        permissions = [sp(permission) for permission in cls.get_permissions(root, info, input) or []]
        return check_standard_create_or_batch_mutation_permissions(permissions, info, cls._meta.verb, input)


class ScopedDjangoFilterDeleteMutation(DjangoFilterDeleteMutation):
    class Meta:
        abstract = True

    @classmethod
    def check_permissions(cls, root, info, input) -> None:
        permissions = [sp(permission) for permission in cls.get_permissions(root, info, input) or []]
        return check_standard_create_or_batch_mutation_permissions(permissions, info, cls._meta.verb, input)
