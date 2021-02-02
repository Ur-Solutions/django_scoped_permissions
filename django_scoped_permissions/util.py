import itertools
import re
from typing import Mapping, Iterable


from django_scoped_permissions.models import ScopedModel

from pydash import get


def create_resolver_from_method(field_name, method):
    from graphql import GraphQLError

    def resolver(object, info, **args):
        if not method(object, info, **args):
            raise GraphQLError("You are not permitted to view this.")

        return getattr(object, field_name)

    return resolver


def create_resolver_from_scopes(field_name: str, permissions: [str]):
    from graphql import GraphQLError
    from django_scoped_permissions.guards import ScopedPermissionGuard

    permission_guard = ScopedPermissionGuard(permissions)

    def resolver(object, info, **args):
        user = info.context.user

        final_scopes = []
        format_variables = []

        field_value = getattr(object, field_name, None)

        field_value_is_scoped_model = isinstance(field_value, ScopedModel)
        object_is_scoped_model = isinstance(object, ScopedModel)

        field_value_base_scopes = [""]
        object_base_scopes = [""]

        context = {}

        if field_value_is_scoped_model:
            field_value_base_scopes = field_value.get_base_scopes()

        if object_is_scoped_model:
            object_base_scopes = object.get_base_scopes()

        # Deprecated
        context["base_scopes"] = field_value_base_scopes
        context["required_scopes"] = field_value_base_scopes
        context["field_scopes"] = object_base_scopes

        granting_permissions = (
            user.get_granting_permissions()
            if hasattr(user, "get_granting_permissions")
            else []
        )

        if not permission_guard.has_permission(granting_permissions, context=context):
            raise GraphQLError("You are not permitted to view this.")

        return field_value

    return resolver


def expand_scopes(
    scopes: Iterable[str], expansion_map: Mapping[str, Iterable[str]] = None
) -> Iterable[str]:
    if expansion_map is None or len(list(expansion_map.values())) == 0:
        return scopes

    # First get all keys of the expansion map.
    keys = list(expansion_map.keys())

    values = expansion_map.values()

    # Now create the cartesian product of all expansion values
    product = itertools.product(*values)

    final_scopes = set()

    # Brilliant, so now we have all the keys, and all the possible permutations of their
    # values. We can now create all the final interpolated scopes
    for permutation in product:
        # Construct the expansion map for this permutation
        permutation_expansion_map = {keys[i]: permutation[i] for i in range(len(keys))}

        for scope in scopes:
            final_scopes.add(scope.format(**permutation_expansion_map))

    return list(final_scopes)


scope_variable_regex = re.compile("{[^{}]+}")


def expand_scopes_from_context(scopes: Iterable[str], context):
    """
    Takes a context object, and expands all scopes. The context object may contain nested dictionaries,
    or other object types.

    To extract the relevant fields from the context, we use pydash.get.

    This method is used to inject appropriate variables into the scope strings. Suppose for instance
    that we have the scope "facilities:{input.facility}:create". The idea here is that we should take
    the input as a context-parameter, and inject the "facility" field into the scope.

    Before sending the variables and scopes to the "expand_scopes" helper method, we translate all
    dots to double underscores. This is to please the str.format method, which attempts to do
    magic itself when getting variables with dots. Using variables with double underscores
    directly in the scopes sent to this method should be unproblematic, but may lead to undefined behaviour.

    Also note that some variables may have multiple target values. This is the case for the magic variable
    {base_scopes}, which can be used for mutations and queries where a singular object of type ScopedModel
    is supplied. This is the case for DjangoPatchMutation, DjangoUpdateMutation and DjangoScopedNode.

    :param scopes:
    :param context:
    :return:
    """

    # First we extract all the variable strings we need to attend to. We prefetch them here, so we
    # can extract them from the context
    variable_strings = []
    new_scopes = []

    for scope in scopes:
        matches = scope_variable_regex.findall(scope)
        for match in matches:
            variable_strings.append(match[1:-1])

        # We translate dots to double underscores here. This is to please
        # the str.format function, as it itself tries to do some magic
        # when receiving dotted variables.
        new_scopes.append(scope.replace(".", "__"))

    extracted_context_values = {
        # We replace the double underscores here as well, so the lookups match
        variable.replace(".", "__"): _overload_context_variable(get(context, variable))
        for variable in variable_strings
    }

    return expand_scopes(new_scopes, extracted_context_values)


def _overload_context_variable(variable):
    """
    This helper method basically ensures a context variable is wrapped in a list
    if it is not a list itself.

    :param variable:
    :return:
    """
    if isinstance(variable, list):
        return variable
    return [variable]
