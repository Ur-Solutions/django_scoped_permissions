from typing import Any, Union, Optional
from django.db.models import Model
from django.db.models.base import ModelBase


def scope_grants_permission(
    required_scope: str, granting_scope: str, verb: Optional[str] = None
):
    """
    scope_grants_permission checks if a single granting scope matches a single required scope.

    This is slightly simpler than the method scopes_grant_permission below, and follows the following rules:

    1. If the granting_scope has an exclusion rule (starts with "-"), we always return false.
    2. If the scopes are equal, we always returns true.
    3. If the granting_scope is an exact rule (starts with "="), we expand the required scope non-recursively with the verb, and then check for equality.
    4. Exapnd the required scope recursively with the verb and check if the scopes match.

    """
    # Single negation permissions will never grant access
    if granting_scope.startswith("-"):
        return False

    if required_scope == granting_scope:
        return True

    # The equal case will not have the verb applied recursively
    if granting_scope.startswith("="):
        expanded_scopes = expand_scopes_with_verb([required_scope], verb)
    else:
        expanded_scopes = expand_scopes_with_verb_recursively([required_scope], verb)

    return any_scope_matches(expanded_scopes, [granting_scope])


def scopes_grant_permissions(
    required_scopes: [str], granting_scopes: [str], verb: Optional[str] = None
):
    """
    scopes_grants_permission takes as arguments a number of required base scopes,
    and then a set of granting scopes, e.g. scopes a User has.
    The method then checks whether or not the granting scopes provides access to the
    required base scopes.
    This depends on multiple facts. But primarily, we check the following:
        1. If the user has an exact negation which matches one of the base_scopes,
           or the base_scopes with the verb expanded, we return False.
        2. If the user has an exact scope which matches one of the base_scopes,
           or the base_scopes with the verb expanded, we return True.
        3. If the user has a negation that matches any of the scopes (expanded or not), we return False.
        4. If the user has a scope that matches any of the scopes, we return True.
        5. Return False
    """
    if len(required_scopes) == 0:
        return True

    exclude_exact, include_exact, exclude, include = partition_scopes(granting_scopes)

    required_base_scopes_with_verb = expand_scopes_with_verb(required_scopes, verb)
    required_scopes_with_verb = expand_scopes_with_verb_recursively(
        required_scopes, verb
    )

    # Check case 1
    if any_scope_matches(required_base_scopes_with_verb, exclude_exact):
        return False

    # Check case 2
    if any_scope_matches(required_base_scopes_with_verb, include_exact):
        return True

    # Check case 3
    if any_scope_matches(required_scopes_with_verb, exclude):
        return False

    # Check case 4
    if any_scope_matches(required_scopes_with_verb, include):
        return True

    return False


def any_scope_matches(required_scopes: [str], scopes: [str]):
    """
    Check if any of the given scopes matches any of the required_scopes.
    :param required_scopes:
    :param scopes:
    :return:
    """

    return any(
        scope_matches(strip_negation(required_scope), strip_negation(scope))
        for required_scope in required_scopes
        for scope in scopes
    )


### HELPERS ###
def expand_scopes_with_verb(scopes: [str], verb: str):
    """
    Appends an verb to the scopes given.
    Example:
        scopes: ["user:1", "company:1:user:1"]
        verb: edit
        [
            "user:1:edit",
            "company:1:user:1:edit",
        ]
    :param scopes:
    :param verb:
    :return:
    """
    if not verb:
        return scopes

    return [create_scope(scope, verb) for scope in scopes]


def expand_scopes_with_verb_recursively(scopes: [str], verb: str):
    """
    Appends an verb to all sub-scopes for every scope in a list of scopes.
    Note that the verb itself is also added to the list.
    Example:
        scopes: ["user:1", "company:1:user:1"]
        verb: edit
        [
            "edit",
            "user:1:edit",
            "user:edit",
            "company:1:user:1:edit",
            "company:1:user:edit",
            "company:1:edit",
            "company:edit"
        ]
    :param scopes:
    :param verb:
    :return:
    """
    if not verb:
        return scopes

    result = [verb]
    for scope in scopes:
        parts = scope.split(":")
        for i in range(len(parts)):
            new_scope = create_scope(*parts[: i + 1], verb)
            result.append(new_scope)

    return result


def scope_matches(required_permission: str, granting_permission: str):
    """
    Checks if two scopes match. They match if and only if the following is true:
        - All parts of required_scope are contained in scope, in the same order as supplied in required_scope.
        - If the scope starts with =, it must match the required scope exactly.
    Examples:
        required    = users:1:edit
        scope       = users:1
        OK
        required    = users:1:edit
        scope       = users:1:create
        NOT OK
        required    = users:1
        scope       = users:1:create
        NOT OK
        required    = company:1:timesheets:create
        scope       = company:1
        OK
    :param required_permission:
    :param granting_permission:
    :return:
    """
    if granting_permission[0] == "=":
        return required_permission == granting_permission[1:]

    if granting_permission == required_permission:
        return True

    # Optimisation, bail out when the wildcard is the only permission
    if granting_permission == "*":
        return True

    required_scopes = required_permission.split(":")
    granting_scopes = granting_permission.split(":")

    # A more specified granting scope can never grant access.
    # E.g.
    #  granting = user:1:create
    #  required = user:1
    if len(granting_scopes) > len(required_scopes):
        return False

    if all(
        granting_scope_part == "*"
        or required_scope_part == "*"
        or (granting_scope_part == required_scope_part)
        for required_scope_part, granting_scope_part in zip(
            required_scopes, granting_scopes
        )
    ):
        return True

    return False


def get_scope_arg_str(arg: Union[str, Model, ModelBase]):
    """
    Converts a scope argument into a string.
    For models and modelbases we lookup the model name.
    """
    if isinstance(arg, Model) or isinstance(arg, ModelBase):
        return arg._meta.model_name
    return str(arg)


def create_scope(*args: [Any]):
    """
    Converts a list of scopes into a scope-string.
    :param args:
    :return:
    """
    return ":".join([get_scope_arg_str(arg) for arg in args])


def partition_scopes(scopes: [str]):
    """
    partition_scopes partitions a set of scopes into four sets:
        - Exclude exact
        - Include exact
        - Exclude
        - Include
    """
    exclude_exact = []
    include_exact = []
    exclude = []
    include = []

    for scope in scopes:
        if scope.startswith("-="):
            exclude_exact.append(scope)
        elif scope.startswith("="):
            include_exact.append(scope)
        elif scope.startswith("-"):
            exclude.append(scope)
        else:
            include.append(scope)

    return [exclude_exact, include_exact, exclude, include]


def strip_negation(scope: str) -> str:
    return scope[1:] if scope.startswith("-") else scope
