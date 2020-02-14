from typing import Any, Union
from django.db.models import Model
from django.db.models.base import ModelBase


def any_scope_matches(required_scopes: [str], scopes: [str]):
    """
    Check if any of the given scopes matches any of the required_scopes.

    We also check whether or not any of the exclude scope in `scopes` matches
    a scope in `required_scopes`. If this is true, we return False

    :param required_scopes:
    :param scopes:
    :return:
    """
    include_scopes = []
    exclude_scopes = []

    for scope in scopes:
        if scope[0] == "-":
            # Remove leading "-", as all checks here-on-out knows that this is an exclude scope
            # due to it being in the exclude_scopes-array
            exclude_scopes.append(scope[1:])
        else:
            include_scopes.append(scope)


    return not any(
        scope_matches(required_scope, scope)
        for required_scope in required_scopes
        for scope in exclude_scopes
    ) and any(
        scope_matches(required_scopes, scope)
        for required_scope in required_scopes
        for scope in include_scopes
    )


### HELPERS ###
def expand_scopes_with_action(scopes: [str], action: str):
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


def read_scoped(qs, user, company, filter_fields={}):
    if user.is_superuser:
        return qs

    model_name = qs.model._meta.model_name
    user_scopes = user.get_scopes()

    negated_read_scope = f"-{model_name}:read"
    if negated_read_scope in user_scopes:
        return qs.none()

    read_scopes = [f"{model_name}:read", f"company:{company.id}", "read"]
    scope_match = any_scope_matches(read_scopes, user_scopes)
    if scope_match:
        return qs

    return qs.filter(**filter_fields)
