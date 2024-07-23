from typing import Optional, List
import re

from django.conf import settings

from django_scoped_permissions.core.check_scoped_permission import overload_scoped_permission_like
from django_scoped_permissions.core.comparison import check_granting_scope_provides_access_to_required_scope
from django_scoped_permissions.core.partitioning import partition_scoped_permissions
from django_scoped_permissions.core.tree import ScopedPermissionTree
from django_scoped_permissions.core.utils import interpolate_context
from django_scoped_permissions.models import StoredScopedPermission

VALID_SCOPE_CHARACTERS = re.compile(r"[a-zA-Z0-9_\-:{}*]+")
VALID_VERB_CHARACTERS = re.compile(r"[a-zA-Z0-9_\-:{}*]+")

type ScopedPermissionLike = str | ScopedPermission | ScopedPermissionTree


class ScopedPermission:
    """
    ScopedPermission is the core class of the library. It describes a single permission requirement.
    """

    @staticmethod
    def create(*args, **kwargs):
        if len(args) == 0 and len(kwargs) == 0:
            raise ValueError("Either a scope or a verb must be supplied")

        if len(args) > 0 and (isinstance(args[0], ScopedPermission) or isinstance(args[0], ScopedPermissionTree)):
            return args[0]

        scope = ""
        verb = ""
        is_negation = kwargs.get("is_negation", False)
        is_exact = kwargs.get("is_exact", False)

        scope_from_kwargs = kwargs.get("scope", None)
        verb_from_kwargs = kwargs.get("verb", None)

        if scope_from_kwargs:
            scope = scope_from_kwargs

        if verb_from_kwargs:
            verb = verb_from_kwargs

        if len(args) == 1:
            scope = args[0]

            if "@" in scope:
                scope, verb = scope.split("@")

        elif scope == "" and len(args) > 0:
            scope = ":".join([str(arg) for arg in args])

        if scope.startswith("-"):
            is_negation = True
            scope = scope[1:]

        if scope.startswith("="):
            is_exact = True
            scope = scope[1:]

        return ScopedPermission(str(scope), str(verb), is_negation, is_exact)

    @staticmethod
    def safe_create(*args, **kwargs):
        default = kwargs.pop("default", False)

        try:
            return ScopedPermission.create(*args, **kwargs)
        except ValueError:
            if default:
                return default
            else:
                return None

    @staticmethod
    def from_model(model: StoredScopedPermission):
        return ScopedPermission(model.scope, model.verb, model.is_negation, model.is_exact)

    def __init__(self, scope: str, verb: Optional[str] = None, is_negation: bool = False, is_exact: bool = False,
                 validate: bool = getattr(settings, "DJANGO_SCOPED_PERMISSIONS_STRICT_MODE", False)):
        self.scope = scope
        self.verb = verb
        self.is_negation = is_negation
        self.is_exact = is_exact

        if validate:
            self.validate()

    def validate(self):
        """
        Validates the scope and verb of the permission.
        """
        if not self.scope:
            raise ValueError("Scope cannot be empty")

        if not VALID_SCOPE_CHARACTERS.fullmatch(self.scope):
            raise ValueError("Invalid scope characters")

        if self.verb and not VALID_VERB_CHARACTERS.fullmatch(self.verb):
            raise ValueError("Invalid verb characters")

    def check_single_granting_permission_access(self, granting_permission: ScopedPermissionLike):
        """
        Checks if this permission, functioning as a required permission, can be accessed by the
        granting permission supplied.

        This is the singular variant of the `check_access` method.

        Note that negations are handled by returning "True" if the granting permission does not match.
        Negations are handled the same if any or both of the permissions are negations; if the permissions
        don't match, we return True.
        """
        is_negation = self.is_negation or granting_permission.is_negation

        if self.is_exact or granting_permission.is_exact:
            return (self.scope == granting_permission.scope) ^ is_negation

        scopes_match = check_granting_scope_provides_access_to_required_scope(
            self.scope,
            granting_permission.scope
        )

        # If the granting permission is a generic permission (has no verb), we
        # grant verb-access by default
        verb_match = check_granting_scope_provides_access_to_required_scope(
            self.verb,
            granting_permission.verb
        ) if self.verb else True

        return (scopes_match and verb_match) ^ is_negation

    def check_access(self, granting_permission: ScopedPermissionLike | List[ScopedPermissionLike]):
        """
        Checks if this permission, functioning as a required permission, can be accessed by the
        granting permission(s) supplied.

        This is the primary method used in this library to check for permission matching. It utilises the
        low-level `check_granting_scope_provides_access_to_required_scope` method to do the actual scope matching.
        """

        # Optimisation, if we only have a single permission, we can skip the partitioning.
        if not isinstance(granting_permission, list):
            return self.check_single_granting_permission_access(granting_permission)

        if len(granting_permission) == 0:
            # If we have no permissions, we can return true only if we are a wildcard and have no verb
            # and is not negated
            return (self.scope == "*" and not self.verb) ^ self.is_negation

        granting_permissions = overload_scoped_permission_like(granting_permission) if not isinstance(
            granting_permission, list) else [
            overload_scoped_permission_like(gp) for gp in granting_permission
        ]

        # The checks are done in four rounds, based on the partitioning of the permissions.
        # The first round checks if an exact exclude match is found, if so
        partitioned_permissions = partition_scoped_permissions(granting_permissions)

        # We do a quick optimisation here and check if we only have include permissions (which is likely). If
        # so we, we simply run an any check on these
        include_permissions = partitioned_permissions["include"]
        if len(include_permissions) == len(granting_permissions):
            return any(
                self.check_single_granting_permission_access(permission) for permission in include_permissions)

        # Otherwise, we have to check all the permission in a particular order. First we check if we have an exact
        # exclude match. This takes highest precedence, and will result in a False.
        # Next we check an exact include match. This takes second-highest precedence, and will result in a True.
        # Then we check an exclude match. This takes third-highest precedence, and will result in a False.
        # Finally, we check an include match.
        exclude_exact_permissions = partitioned_permissions["exclude_exact"]

        if len(exclude_exact_permissions) > 0:
            # For exclude permissions we need all to "pass" in order to return True
            return all(
                self.check_single_granting_permission_access(permission) for permission in exclude_exact_permissions)

        include_exact_permissions = partitioned_permissions["include_exact"]
        if len(include_exact_permissions) > 0:
            return any(
                self.check_single_granting_permission_access(permission) for permission in include_exact_permissions)

        exclude_permissions = partitioned_permissions["exclude"]
        if len(exclude_permissions) > 0:
            return all(self.check_single_granting_permission_access(permission) for permission in exclude_permissions)

        include_permissions = partitioned_permissions["include"]
        if len(include_permissions) > 0:
            return any(self.check_single_granting_permission_access(permission) for permission in include_permissions)

        return False

    def apply_context(self, context):
        """
        Creates a new permission with the context applied
        """
        return ScopedPermission(
            interpolate_context(self.scope, context),
            interpolate_context(self.verb, context),
            is_negation=self.is_negation,
            is_exact=self.is_exact
        )

    def __str__(self):
        result = ""

        if self.is_negation:
            result += "-"
        if self.is_exact:
            result += "="

        result += self.scope

        if self.verb:
            result += f"@{self.verb}"

        return result

    def __hash__(self):
        return hash((self.scope, self.verb, self.is_negation, self.is_exact))

    def __eq__(self, other):
        if isinstance(other, ScopedPermission):
            return self.scope == other.scope and self.verb == other.verb and self.is_negation == other.is_negation and self.is_exact == other.is_exact

        return False

    def __or__(self, other):
        return ScopedPermissionTree(None, self, other, "OR")

    def __and__(self, other):
        return ScopedPermissionTree(None, self, other, "AND")

    def __xor__(self, other):
        return ScopedPermissionTree(None, self, other, "XOR")

    def __invert__(self):
        return ScopedPermission(
            self.scope,
            self.verb,
            is_negation=not self.is_negation,
            is_exact=self.is_exact
        )


sp = ScopedPermission.create
