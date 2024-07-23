def check_granting_scope_provides_access_to_required_scope(required_scope: str, granting_scope: str):
    """
    Checks if two scopes match. They match if and only if the following is true:
        - All parts of required_scope are contained in scope, in the same order as supplied in required_scope.
        - If the scope starts with =, it must match the required scope exactly.
    Examples:
        required    = users:1:vehicles
        granting    = users:1
        OK

        required    = users:1:vehicles
        granting    = users:1:stamps
        NOT OK

        required    = users:1
        granting    = users:1:vehicles
        NOT OK

        required    = company:1:vehicles:parts
        granting    = company:1
        OK
    :param required_scope:
    :param granting_scope:
    :return:
    """
    if granting_scope == required_scope:
        return True

    # Optimisation, bail out when the wildcard is the only permission
    if granting_scope == "*" or required_scope == "*":
        return True

    required_scopes = required_scope.split(":")
    granting_scopes = granting_scope.split(":")

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
