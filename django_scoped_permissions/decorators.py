from functools import wraps

from django.core.exceptions import PermissionDenied

from django_scoped_permissions.guards import ScopedPermissionGuard


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
