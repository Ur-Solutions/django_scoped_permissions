

def create_scoped_permission(
        *args,
        **kwargs
):

    scope = ""
    verb = ""

    scope_from_kwargs = kwargs.get("scope", None)
    verb_from_kwargs = kwargs.get("verb", None)

    if scope_from_kwargs:
        scope = scope_from_kwargs

    if verb_from_kwargs:
        verb = verb_from_kwargs

    if scope == "":
        scope = ":".join(args)

    permission = scope

    if verb != "":
        permission = f"{permission}@{verb}"

    return permission
