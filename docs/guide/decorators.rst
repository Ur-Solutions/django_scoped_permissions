=================================
Decorators
=================================

The library supplies two decorators to use with graphql queries/mutations and with functional views, respectively:

 * :code:`gql_has_scoped_permissions`
 * :code:`function_has_scoped_permissions`

The functions take the same arguments: Either a ScopedPermissionGuard, a combination of these, or the same inputs as a
ScopedPermissionGuard would take. See :ref:`guards` for more info.

Some examples:

.. code-block:: python

    @gql_has_scoped_permissions("scope1:scope2")
    def resolve_something(self, info, **kwargs):
        return None

    @gql_has_scoped_permissions(scope="scope1:scope2", verb="read")
    def resolve_something_else(self, info, **kwargs):
        return None

    @gql_has_scoped_permissions(
        ScopedPermissionGuard("scope1:scope2") & ScopedPermissionGuard("scope3") |
        (
            ScopedPermissionGuard("scope4") ^ ScopedPermissionGuard("scope5")
        )
    )
    def resolve_something_very_guarded(self, info, **kwargs):
        return None

.. code-block:: python

    @function_has_scoped_permissions("scope1:scope2")
    def handle_something(request):
        return None

    @function_has_scoped_permissions(scope="scope1:scope2", verb="read")
    def handle_something_else(request):
        return None

    @function_has_scoped_permissions(
        ScopedPermissionGuard("scope1:scope2") & ScopedPermissionGuard("scope3") |
        (
            ScopedPermissionGuard("scope4") ^ ScopedPermissionGuard("scope5")
        )
    )
    def handle_something_very_guarded(request):
        return None


