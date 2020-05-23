from typing import Any, Union, Optional
from django.db.models import Model
from django.db.models.base import ModelBase


def scopes_grant_permissions(
        required_base_scopes: [str], granting_scopes: [str], action: Optional[str] = None
):
    """
    scopes_grants_permission takes as arguments a number of required base scopes,
    and then a set of granting scopes, e.g. scopes a User has.
    The method then checks whether or not the granting scopes provides access to the
    required base scopes.
    This depends on multiple facts. But primarily, we check the following:
        1. If the user has an exact negation which matches one of the base_scopes,
           or the base_scopes with the action expanded, we return False.
        2. If the user has an exact scope which matches one of the base_scopes,
           or the base_scopes with the action expanded, we return True.
        3. If the user has a negation that matches any of the scopes (expanded or not), we return False.
        4. If the user has a scope that matches any of the scopes, we return True.
        5. Return False
    """
    exclude_exact, include_exact, exclude, include = partition_scopes(granting_scopes)

    required_base_scopes_with_action = expand_scopes_with_action(
        required_base_scopes, action
    )
    required_scopes_with_action = expand_scopes_with_action_recursively(
        required_base_scopes, action
    )

    # Check case 1
    if any_scope_matches(required_base_scopes_with_action, exclude_exact):
        return False

    # Check case 2
    if any_scope_matches(required_base_scopes_with_action, include_exact):
        return True

    # Check case 3
    if any_scope_matches(required_scopes_with_action, exclude):
        return False

    # Check case 4
    if any_scope_matches(required_scopes_with_action, include):
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
def expand_scopes_with_action(scopes: [str], action: str):
    """
    Appends an action to the scopes given.
    Example:
        scopes: ["user:1", "company:1:user:1"]
        action: edit
        [
            "user:1:edit",
            "company:1:user:1:edit",
        ]
    :param scopes:
    :param action:
    :return:
    """
    if not action:
        return scopes

    return [create_scope(*scope, action) for scope in scopes]


def expand_scopes_with_action_recursively(scopes: [str], action: str):
    """
    Appends an action to all sub-scopes for every scope in a list of scopes.
    Note that the action itself is also added to the list.
    Example:
        scopes: ["user:1", "company:1:user:1"]
        action: edit
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
    :param action:
    :return:
    """
    if not action:
        return scopes

    result = [action]
    for scope in scopes:
        parts = scope.split(":")
        for i in range(len(parts)):
            new_scope = create_scope(*parts[: i + 1], action)
            result.append(new_scope)

    return result


def scope_matches(required_scope: str, scope: str):
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
    :param required_scope:
    :param scope:
    :return:
    """
    if scope[0] == "=":
        return required_scope == scope[1:]

    return scope in required_scope


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
