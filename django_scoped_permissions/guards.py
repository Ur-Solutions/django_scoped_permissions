from typing import Optional, List, Union

from django_scoped_permissions.core import scopes_grant_permissions
from django_scoped_permissions.util import expand_scopes_from_context


class ScopedPermissionRequirement:
    """
    ScopedPermissionRequirement describes a single permission requirement. A ScopedPermissionGuard
    holds one or more such requirements to describe a complex permission guard.
    """

    def __init__(self, scope: str, verb: Optional[str] = None):
        self.scope = scope
        self.verb = verb


def _evaluate_value(value, granting_scopes: List[str], context=None):
    if not context:
        context = {}

    granting_scopes = expand_scopes_from_context(granting_scopes, context)

    if isinstance(value, SPRBinOp) or isinstance(value, SPRUnOp):
        return value.has_permission(granting_scopes, context)
    elif isinstance(value, str):
        required_scopes = expand_scopes_from_context([value], context)
        return scopes_grant_permissions(required_scopes, granting_scopes)
    elif isinstance(value, list):
        required_scopes = expand_scopes_from_context(value, context)
        return scopes_grant_permissions(required_scopes, granting_scopes)
    elif isinstance(value, ScopedPermissionRequirement):
        required_scopes = expand_scopes_from_context([value.scope], context)
        return scopes_grant_permissions(required_scopes, granting_scopes, value.verb)
    elif isinstance(value, bool):
        return value
    else:
        return False


class SPRUnOp:
    def __init__(self, value):
        self.value = value

    def has_permission(self, granting_scopes: List[str], context=None):
        return _evaluate_value(self.value, granting_scopes, context)


class SPRBinOp:
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

    def has_permission(self, granting_scopes: List[str], context=None):
        return False

    def lhs_has_permission(self, granting_scopes: List[str], context=None):
        return _evaluate_value(self.lhs, granting_scopes, context)

    def rhs_has_permission(self, granting_scopes: List[str], context=None):
        return _evaluate_value(self.rhs, granting_scopes, context)


class SPRAnd(SPRBinOp):
    def has_permission(self, granting_scopes: List[str], context=None):
        return self.lhs_has_permission(granting_scopes) & self.rhs_has_permission(
            granting_scopes
        )


class SPROr(SPRBinOp):
    def has_permission(self, granting_scopes: List[str], context=None):
        return self.lhs_has_permission(
            granting_scopes, context
        ) | self.rhs_has_permission(granting_scopes, context)


class SPRXor(SPRBinOp):
    def has_permission(self, granting_scopes: List[str], context=None):
        return self.lhs_has_permission(
            granting_scopes, context
        ) ^ self.rhs_has_permission(granting_scopes, context)


class SPRNot(SPRUnOp):
    def __init__(self, value):
        self.value = value

    def has_permission(self, granting_scopes: List[str], context=None):
        return not super().has_permission(granting_scopes, context)


class ScopedPermissionGuard:
    """
    ScopedPermissionGuard represents a complex permission guard, guarding some resource.

    The guard may contain a single permission requirement, or multiple.
    """

    def __init__(self, *args, **kwargs):
        # Set a default to False
        self.root = SPRUnOp(False)
        self.__overload_args_kwargs(*args, **kwargs)

    def __overload_args_kwargs(self, *args, **kwargs):
        if "scope" in kwargs:
            scope = kwargs["scope"]
            verb = kwargs.get("verb", None)
            self.root = SPRUnOp(ScopedPermissionRequirement(scope, verb))
        elif len(args) == 1:
            if "verb" in kwargs and isinstance(args[0], str):
                self.root = SPRUnOp(ScopedPermissionRequirement(args[0], args[1]))
            else:
                self.root = self._get_overloaded_arg(args[0])
        elif len(args) == 2 and isinstance(args[0], str) and isinstance(args[1], str):
            self.root = SPRUnOp(ScopedPermissionRequirement(args[0], args[1]))
        else:
            self.root = self._get_overloaded_arg(args[0])

            for arg in args[1:]:
                self.root = SPROr(self.root, self._get_overloaded_arg(arg))

    def _get_overloaded_arg(self, arg):
        if isinstance(arg, str):
            return SPRUnOp(ScopedPermissionRequirement(arg))
        elif isinstance(arg, (tuple, list)) and len(arg) == 2:
            return SPRUnOp(ScopedPermissionRequirement(arg[0], arg[1]))
        elif isinstance(arg, ScopedPermissionRequirement):
            return SPRUnOp(arg)
        elif isinstance(arg, ScopedPermissionGuard):
            return arg.root
        elif isinstance(arg, (SPRBinOp, SPRUnOp)):
            return arg
        elif isinstance(arg, (tuple, list)):
            if len(arg) == 0:
                return SPRUnOp(False)

            base = self._get_overloaded_arg(arg[0])

            for arg in arg[1:]:
                base = SPROr(base, self._get_overloaded_arg(arg))

            return base
        else:
            return SPRUnOp(False)

    def has_permission(self, granting_scopes: Union[List[str], str], context=None):
        if isinstance(granting_scopes, str):
            granting_scopes = [granting_scopes]
        return self.root.has_permission(granting_scopes, context)

    def __and__(self, other):
        # Always create a new instance
        guard = ScopedPermissionGuard(self.root)
        guard.root = SPRAnd(guard.root, other.root)
        return guard

    def __or__(self, other):
        # Always create a new instance
        guard = ScopedPermissionGuard(self.root)
        guard.root = SPROr(guard.root, other.root)
        return guard

    def __xor__(self, other):
        # Always create a new instance
        guard = ScopedPermissionGuard(self.root)
        guard.root = SPRXor(guard.root, other.root)
        return guard

    def __invert__(self):
        # Always create a new instance
        guard = ScopedPermissionGuard(self.root)
        guard.root = SPRNot(guard.root)
        return guard

    def __len__(self):
        # Temporary to work around graphene-django-cuds length requirement for permissions
        return 1
