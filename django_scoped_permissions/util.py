import itertools
import re

from graphql import GraphQLError
from typing import Mapping, Iterable, Union, List, TYPE_CHECKING

from django_scoped_permissions.models import ScopedModel, ProtectedModelMixin

from pydash import get

if TYPE_CHECKING:
    from django_scoped_permissions.core.scoped_permission import ScopedPermissionLike
    from django_scoped_permissions.core.scoped_permission import ScopedPermission, sp


def create_resolver_from_method(field_name, method):
    def resolver(object, info, **args):
        if not method(object, info, **args):
            raise GraphQLError("You are not permitted to view this.")

        return getattr(object, field_name)

    return resolver


def create_resolver_from_scopes(field_name: str,
                                permissions: "ScopedPermissionLike"):
    required_permission = sp(permissions)

    def resolver(object, info, **args):
        user = info.context.user

        field_value = getattr(object, field_name, None)

        field_value_is_protected_model = isinstance(field_value, ProtectedModelMixin)
        object_is_protected_model = isinstance(object, ScopedModel)

        field_value_required_permissions = [""]
        object_required_permissions = [""]

        context = {}

        if field_value_is_protected_model:
            field_value_required_permissions = field_value.get_required_permissions()

        if object_is_protected_model:
            object_required_permissions = object.get_required_permissions()

        # Deprecated
        context["base_scopes"] = field_value_required_permissions
        context["required_scopes"] = field_value_required_permissions
        context["field_scopes"] = object_required_permissions

        granting_permissions = (
            user.get_granting_permissions(context)
            if hasattr(user, "get_granting_permissions")
            else []
        )

        if not required_permission.apply_context(context).check_access(granting_permissions):
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
