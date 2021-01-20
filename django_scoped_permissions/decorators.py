from functools import wraps

from django.core.exceptions import PermissionDenied

from django_scoped_permissions.util import expand_scopes_from_context


def gql_has_scoped_permissions(
    *permissions, fail_message: str = "You are not permitted to view this",
):
    """
    gql_has_permissions is a function which wraps a `resolve_<x>` or
    `mutate` field for any GraphQL object.

    When called, it checks whether or not the calling user has permission to
    authorize the resource being requested, depending on the permissions given
    as necessary to access the resource.

    :param permissions: The permission required to access the wrapped resource.
    :param fail_to_none: If true, and the user is not authorized, the field will resolve to None.
                            If false, the entire query will fail dramatically in a 401.
    :param fail_message: If fail_to_none is false, and the permission fails, this variable determines
                         the string which is thrown in the exception.
    :param fail_to_lambda: If not none, and the permission fails, this variable (assumed to be a function)
                           will be called.
    :return:
    """

    def decorator(func):
        @wraps(func)
        def wrapper(cls, info, *args, **kwargs):
            if not hasattr(info, "context") or not hasattr(info.context, "user"):
                raise PermissionDenied(fail_message)

            context = {}
            context["context"] = info.context
            context["user"] = info.context.user
            expanded_permissions = expand_scopes_from_context(permissions, context)

            user = info.context.user
            if (
                (not user or user.is_anonymous)
                and len(expanded_permissions) > 0
                or not user.has_any_scoped_permissions(*expanded_permissions)
            ):
                raise PermissionDenied(fail_message)
            return func(cls, info, *args, **kwargs)

        return wrapper

    return decorator


gql_has_any_scoped_permissions = gql_has_scoped_permissions


def gql_has_all_scoped_permissions(
    *permissions, fail_message: str = "You are not permitted to view this",
):
    """
    gql_has_permissions is a function which wraps a `resolve_<x>` or
    `mutate` field for any GraphQL object.

    When called, it checks whether or not the calling user has permission to
    authorize the resource being requested, depending on the permissions given
    as necessary to access the resource.

    :param permissions: The permission required to access the wrapped resource.
    :param fail_to_none: If true, and the user is not authorized, the field will resolve to None.
                            If false, the entire query will fail dramatically in a 401.
    :param fail_message: If fail_to_none is false, and the permission fails, this variable determines
                         the string which is thrown in the exception.
    :param fail_to_lambda: If not none, and the permission fails, this variable (assumed to be a function)
                           will be called.
    :return:
    """

    def decorator(func):
        @wraps(func)
        def wrapper(cls, info, *args, **kwargs):
            if not hasattr(info, "context") or not hasattr(info.context, "user"):
                raise PermissionDenied(fail_message)

            context = {}
            context["context"] = info.context
            context["user"] = info.context.user
            expanded_permissions = expand_scopes_from_context(permissions, context)

            user = info.context.user
            if (
                (not user or user.is_anonymous)
                and len(permissions) > 0
                or not user.has_all_scoped_permissions(*expanded_permissions)
            ):
                raise PermissionDenied(fail_message)
            return func(cls, info, *args, **kwargs)

        return wrapper

    return decorator
