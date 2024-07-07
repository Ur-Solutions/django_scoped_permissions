import typing
from typing import Union, Literal
from django_scoped_permissions.core.check_scoped_permission import overload_scoped_permission_like

from typing import Optional

OP_AND = "AND"
OP_OR = "OR"
OP_XOR = "XOR"

type TreeBinaryOperator = Literal["AND", "OR", "XOR"]
type ScopedPermissionTreeLike = ScopedPermission | ScopedPermissionTree

if typing.TYPE_CHECKING:
    from django_scoped_permissions.core.scoped_permission import ScopedPermissionLike, ScopedPermission


class ScopedPermissionTree:

    def __init__(self, value: Optional["ScopedPermission"], left: Optional[ScopedPermissionTreeLike] = None,
                 right: Optional[ScopedPermissionTreeLike] = None, operator: TreeBinaryOperator = OP_AND):

        if value is None and left is None and right is None:
            raise ValueError("A ScopedPermissionTree must have either a value or a left side and right side")

        if value is not None and left is not None:
            raise ValueError("A ScopedPermissionTree cannot have both a value and a left side")

        if value is None and (left is None or right is None):
            raise ValueError("A ScopedPermissionTree must have both a left side and a right side")

        self.value = value
        self.left = left if isinstance(left, ScopedPermissionTree) else ScopedPermissionTree(left, None, None)
        self.right = right if isinstance(right, ScopedPermissionTree) else ScopedPermissionTree(right, None, None)
        self.operator = operator

    def check_access(self, granting_permission: "ScopedPermissionLike" | typing.List["ScopedPermissionLike"]):
        """
        Checks if this permission, functioning as a required permission, can be accessed by the
        granting permission supplied.
        """

        if isinstance(granting_permission, list):
            return any(self.check_access(gp) for gp in granting_permission)

        granting_permission = overload_scoped_permission_like(granting_permission)

        if self.value is not None:
            return self.value.check_access(granting_permission)

        match self.operator:
            case "AND":
                return self.left.check_access(granting_permission) and self.right.check_access(granting_permission)
            case "OR":
                return self.left.check_access(granting_permission) or self.right.check_access(granting_permission)
            case "XOR":
                return self.left.check_access(granting_permission) ^ self.right.check_access(granting_permission)
            case _:
                raise ValueError(f"Unknown operator {self.operator}")

    def apply_context(self, context):
        """
        Creates a new permission tree with the context applied
        """
        if self.value is not None:
            return self.value.apply_context(context)

        if self.left is not None:
            self.left.apply_context(context)

        if self.right is not None:
            self.right.apply_context(context)

    def is_leaf(self):
        return self.value is not None

    def is_branch(self):
        return self.left is None and self.right is None

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        if self.value is not None:
            return str(self.value)

        return f"({str(self.left)} <> {str(self.right)})"

    def __or__(self, other):
        return ScopedPermissionTree(None, self, other, "OR")

    def __and__(self, other):
        return ScopedPermissionTree(None, self, other, "AND")

    def __xor__(self, other):
        return ScopedPermissionTree(None, self, other, "XOR")

    def __invert__(self):
        if self.is_leaf():
            return ScopedPermissionTree(~self.value, None, None)

        match self.operator:
            case "AND":
                return ScopedPermissionTree(None, ~self.left, ~self.right, "OR")
            case "OR":
                return ScopedPermissionTree(None, ~self.left, ~self.right, "AND")
            case "XOR":
                return ScopedPermissionTree(None, ~self.left, ~self.right, "XOR")
            case _:
                raise ValueError(f"Unknown operator {self.operator}")
