from functools import wraps

from django.core.exceptions import PermissionDenied
from graphene_django_cud.util import disambiguate_id
from graphql.type.definition import GraphQLResolveInfo
from pydash import omit
from typing_extensions import deprecated

from django_scoped_permissions.core.scoped_permission import sp, ScopedPermission
from django_scoped_permissions.guards import ScopedPermissionGuard


def _get_info_from_args(args):
    """
    When resolving the "info" argument, we might need
    to look in more than one place, as whether or not the
    wrapped function is a class method or not will determine
    where the "info" argument is passed.
    """
    for arg in args:
        if isinstance(arg, GraphQLResolveInfo):
            return arg

    return None


def _default_context_resolver(request, resolve_info, *args, **kwargs):
    """
    This is the default method that creates context for the permission
    resolution decorators.

    It adds the request object, and the info object for gql methods,
    the user object and the disambiguated "id" argument of the function,
    if it exists.
    """
    context = {
        "request": request,
        "resolve_info": resolve_info,
        "user": request.user
    }

    if "id" in kwargs:
        context["id"] = disambiguate_id(kwargs["id"])

    return {
        **context,
        **omit(kwargs, "id"),
    }


def protect_view(
        *args,
        fail_message: str = "You are not permitted to view this",
        **kwargs,
):
    fn = kwargs.pop("fn", None)

    if fn and not callable(fn):
        raise ValueError("fn must be a callable")

    resolve_context = kwargs.pop("resolve_context", None)
    permission = ScopedPermission.safe_create(*args, **kwargs, default=sp("*"))

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, "user"):
                raise PermissionDenied(fail_message)

            user = request.user
            if not user or user.is_anonymous:
                raise PermissionDenied(fail_message)

            context = _default_context_resolver(request, None, *args, **kwargs)

            if fn:
                result = fn(request, *args, **kwargs)

                if result is False:
                    raise PermissionDenied(fail_message)

                return func(request, *args, **kwargs)

            if resolve_context and callable(resolve_context):
                result = resolve_context(request, *args, **kwargs)

                if isinstance(result, dict):
                    context.update(result)

            if not permission.apply_context(context).check_access(user.get_granting_permissions(context)):
                raise PermissionDenied(fail_message)

            return func(request, *args, **kwargs)

        return wrapper

    return decorator


def protect_field(
        *args,
        fail_message: str = "You are not permitted to view this",
        **kwargs,
):
    fn = kwargs.pop("fn", None)

    if fn and not callable(fn):
        raise ValueError("fn must be a callable")

    resolve_context = kwargs.pop("resolve_context", None)

    # Create a dummy permission when fn is supplied, just so the sp constructor doesn't fail
    permission = ScopedPermission.safe_create(*args, **kwargs, default=sp("*"))

    def decorator(func):
        @wraps(func)
        def wrapper(cls_or_self, *args, **kwargs):

            info = _get_info_from_args(args)

            if not hasattr(info, "context") or not hasattr(info.context, "user"):
                raise PermissionDenied(fail_message)

            user = info.context.user
            if not user or user.is_anonymous:
                raise PermissionDenied(fail_message)

            if fn:
                result = fn(info.context, *args, **kwargs)

                if result is False:
                    raise PermissionDenied(fail_message)

                return func(cls_or_self, info, *args, **kwargs)

            context = _default_context_resolver(info.context, info, *args, **kwargs)

            if resolve_context and callable(resolve_context):
                result = resolve_context(info, *args, **kwargs)

                if isinstance(result, dict):
                    context.update(result)

            if not permission.apply_context(context).check_access(user.get_granting_permissions(context)):
                raise PermissionDenied(fail_message)

            return func(cls_or_self, *args, **kwargs)

        return wrapper

    return decorator


@deprecated("Use `protect_field`")
def gql_has_scoped_permissions(
        *args,
        fail_message: str = "You are not permitted to view this",
        **kwargs,
):
    """
    gql_has_permissions is a function which wraps a `resolve_<x>` or
    `mutate` field for any GraphQL object.

    When called, it checks whether or not the calling user has permission to
    authorize the resource being requested, depending on the permissions given
    as necessary to access the resource.

    :param permissions: The permission required to access the wrapped resource.
    :param fail_message: If fail_to_none is false, and the permission fails, this variable determines
                         the string which is thrown in the exception.
    :return:
    """

    guard = ScopedPermissionGuard(*args, **kwargs)

    def decorator(func):
        @wraps(func)
        def wrapper(cls, info, *args, **kwargs):
            if not hasattr(info, "context") or not hasattr(info.context, "user"):
                raise PermissionDenied(fail_message)

            user = info.context.user
            if not user or user.is_anonymous:
                raise PermissionDenied(fail_message)

            context = {}
            context["context"] = info.context
            context["user"] = info.context.user

            if not guard.has_permission(user.get_granting_scopes(), context):
                raise PermissionDenied(fail_message)

            return func(cls, info, *args, **kwargs)

        return wrapper

    return decorator


@deprecated("Use `protect_view` instead")
def function_has_scoped_permissions(
        *args,
        fail_message: str = "You are not permitted to view this",
        **kwargs,
):
    guard = ScopedPermissionGuard(*args, **kwargs)

    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not hasattr(request, "user"):
                raise PermissionDenied(fail_message)

            user = request.user
            if not user or user.is_anonymous:
                raise PermissionDenied(fail_message)

            context = {}
            context["context"] = request
            context["user"] = request.user

            if not guard.has_permission(user.get_granting_scopes(), context):
                raise PermissionDenied(fail_message)

            return func(request, *args, **kwargs)

        return wrapper

    return decorator
