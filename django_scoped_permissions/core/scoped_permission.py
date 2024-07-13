from typing import Optional, List
import re

from django.conf import settings

from django_scoped_permissions.core.check_scoped_permission import overload_scoped_permission_like
from django_scoped_permissions.core.comparison import check_scopes_grant_access
from django_scoped_permissions.core.tree import ScopedPermissionTree
from django_scoped_permissions.core.utils import interpolate_context
from django_scoped_permissions.models import StoredScopedPermission

VALID_SCOPE_CHARACTERS = re.compile(r"[a-zA-Z0-9_\-:{}]+")
VALID_VERB_CHARACTERS = re.compile(r"[a-zA-Z0-9_\-{}]+")

type ScopedPermissionLike = str | ScopedPermission | ScopedPermissionTree


class ScopedPermission:
    """
    ScopedPermission is the core class of the library. It describes a single permission requirement.
    """

    @staticmethod
    def create(*args, **kwargs):

        if isinstance(args[0], ScopedPermission) or isinstance(args[0], ScopedPermissionTree):
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
    def safe_create(*args, default: Optional["ScopedPermission"] = None, **kwargs):
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

    def check_access(self, granting_permission: ScopedPermissionLike | List[ScopedPermissionLike]):
        """
        Checks if this permission, functioning as a required permission, can be accessed by the
        granting permission supplied.
        """

        if isinstance(granting_permission, list):
            return any(self.check_access(gp) for gp in granting_permission)

        granting_permission = overload_scoped_permission_like(granting_permission)

        # If both permissions have verbs, and they are not equal, access is definitely not granted
        if self.verb and granting_permission.verb and self.verb != granting_permission.verb:
            return False

        # We do a quick optimisation here and check if the granting_permission is a root-level wildcard
        # If so, we can return true immediately
        if granting_permission.scope == "*" and (
                granting_permission.verb is None or granting_permission.verb == "" or granting_permission.verb == "*"):
            return True

        scopes_match = check_scopes_grant_access(
            self.scope,
            granting_permission.scope
        )

        # If the scopes do not match, access is definitely not granted
        if not scopes_match:
            return False

        # If the scopes match, we need to check if we have a verb match. We have checked the case where
        # both verbs are given and are unequal above.
        if self.verb == granting_permission.verb:
            return True

        # If neither are given, we can return true
        if not self.verb and not granting_permission.verb:
            return True

        # If only the requirement has a verb, we can return true
        if not self.verb and granting_permission.verb:
            return True

        # Otherwise, the granting permission has a verb, and we do not. This means that the
        # granting permission is scoped to a verb, but we require a general access
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
