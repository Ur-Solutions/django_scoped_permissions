from typing import Any


def any_scope_matches(required_scopes: [str], scopes: [str]):
    """
    Check if any of the given scopes matches any of the required_scopes.
    :param required_scopes:
    :param scopes:
    :return:
    """
    return any(
        scope_matches(required_scope, scope)
        for required_scope in required_scopes
        for scope in scopes
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
        All parts of required_scope are contained in scope, in the same order as supplied in required_scope, and scope does not begin with "-"
    Fortunately we can check this easily using the in operator.
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
    return scope[0] != "-" and scope in required_scope


def create_scope(*args: [Any]):
    """
    Converts a list of scopes into a scope-string.
    :param args:
    :return:
    """
    return ":".join([str(arg) for arg in args])
