import re

from django.conf import settings
from pydash import get

variable_regex = re.compile("{[^{}]+}")


def interpolate_context(value: str, context: dict,
                        strict_mode: bool = getattr(settings, "DJANGO_SCOPED_PERMISSIONS_STRICT_MODE", True)):
    """
    Interpolates a string with a context dictionary.

    The variables in the string are surrounded by curly braces, e.g. {var}.

    If there are variables that are not expanded, an exception will be thrown if we are in strict mode.
    """

    if not context:
        return value

    # First we extract all the variable strings we need to attend to. We prefetch them here, so we
    # can extract them from the context
    variable_strings = []
    new_value = value

    for match in variable_regex.findall(value):
        variable_strings.append(match[1:-1])

    extracted_context_values = {
        variable: get(context, variable, "")
        for variable in variable_strings
    }

    if strict_mode:
        for variable, value in extracted_context_values.items():
            if value is None:
                raise Exception(f"Variable {variable} not found in context")

    for variable, value in extracted_context_values.items():
        new_value = new_value.replace(f"{{{variable}}}", str(value))

    return new_value
