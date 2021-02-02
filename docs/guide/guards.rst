==================================
Guards
==================================

Sometimes, we need more complex permission matching than just simple matching between two sets of scopes.
We might for instance need to match on something like: "Does the user have x OR (y and z) BUT NOT w".

For this purpose, we have the class :code:`ScopedPermissionGuard`.

Most decorators and permission-attributes in this library can take ScopedPermissionGuard(s) as arguments. And indeed,
most of them use this class under-the-hood.

Basic usage
---------------------------------

ScopedPermissionGuards in its most simple usage take one or two arguments:

.. code-block:: python

    from django_scoped_permissions.guards import ScopedPermissionGuard

    ScopedPermissionGuard("scope1:scope2")
    ScopedPermissionGuard("scope1", "verb")
    # Can also be supplied by kwargs
    ScopedPermissionGuard(scope="scope1", verb="read")


The guards can verify that a set of granting permissions has access via the `has_permission` method:

.. code-block:: python

    from django_scoped_permissions.guards import ScopedPermissionGuard

    guard = ScopedPermissionGuard(scope="scope1", verb="read")

    assert guard.has_permission("scope1")
    assert guard.has_permission("scope1:read")
    assert guard.has_permission(["read", "scope3"])
    assert not guard.has_permission("scope2")


Combining guards and operators
--------------------------------
The power of guards, however, is unleashed when we combine guards with boolean operators. E.g:

.. code-block:: python

    from django_scoped_permissions.guards import ScopedPermissionGuard

    guard_1 = ScopedPermissionGuard(scope="scope1", verb="read")
    guard_2 = ScopedPermissionGuard("scope2")

    # This guard requires you to have scope1:read AND scope2
    guard_3 = guard_1 & guard_2

    # This guard requires you to have scope1:read OR NOT scope2
    guard_4 = guard_1 | ~guard_2

    # This guard requires you to have scope1:read and scope2 XOR (not scope1 and scope3)
    guard_5 = (guard_1 and guard_2) ^ (ScopedPermissionGuard("scope1") and ScopedPermissionGuard("scope3"))

    assert guard_4.has_permission(["scope1", "scope2"])
    assert guard_4.has_permission(["scope3"])
    assert not guard_4.has_permission(["scope3", "scope2"])

    assert guard_5.has_permission(["scope1:read", "scope2"])
    assert guard_5.has_permission(["scope3"])


Supported operators are:

 * :code:`&`: AND
 * :code:`|`: OR
 * :code:`^`: XOR
 * :code:`~`: NOT



Usage in practice
------------------------------

ScopedPermissionGuards can be used in all decorators and properties where permissions are supplied:


.. code-block:: python

    @gql_has_permission(
        ScopedPermissionGuard(
            scope="user", verb="read") &
        ScopedPermissionGuard("organization:{context.organization.id}:read")
    )
    def resolve_company_user(self, info, **kwargs):
        pass
