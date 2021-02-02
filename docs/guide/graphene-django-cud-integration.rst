=================================
Graphene Django CUD integration
=================================

This library also integrates cleanly with Graphene Django Cud by providing the following mutations:

* :code:`ScopedDjangoCreateMutation`
* :code:`ScopedDjangoUpdateMutation`
* :code:`ScopedDjangoPatchMutation`
* :code:`ScopedDjangoDeleteMutation`
* :code:`ScopedDjangoBatchDeleteMutation`
* :code:`ScopedDjangoFilterDeleteMutation`

These can be split into two groups: Those that alter specific objects, and those that don't.

Object-specific mutations
--------------------------------
Those that do, work very similar to the :ref:`last section<Graphene Integration>`.

For instance:

.. code-block:: python

    from django_scoped_permissions.graphql import ScopedDjangoUpdateMutation

    class UpdateUserMutation(ScopedDjangoUpdateMutation):
        class Meta:
            model = User


Using this mutation will require access to the object, as specified by the object's :code:`get_required_scopes` method.

You can also customize the permissions required by using the `permissions` property:


.. code-block:: python

    from django_scoped_permissions.graphql import ScopedDjangoUpdateMutation

    class UpdateUserMutation(ScopedDjangoUpdateMutation):
        class Meta:
            model = User
            # E.g.
            permissions = (
                "users:update",
                "{required_scopes}
            )

            # or e.g.
            permissions = (
                "company:{context.company.id}:update-users
            )

            # Or e.g.
            permissions = ScopedPermissionGuard(scope="users", verb="update")



Other mutations
--------------------------------

Mutations that don't alter specific objects do not have any default permission implementation, and requires you to
fill out the permissions property.

.. code-block:: python

    from django_scoped_permissions.graphql import ScopedDjangoUpdateMutation

    class CreateUserMutation(ScopedDjangoCreateMutation):
        class Meta:
            model = User
            # E.g.
            permissions = (
                "users:create",
            )

            # or e.g.
            permissions = (
                "company:{context.company.id}:create-users
            )

            # Or e.g.
            permissions = ScopedPermissionGuard(scope="users", verb="update")

