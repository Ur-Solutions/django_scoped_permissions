.. _Graphene Integration

=================================
Graphene integration
=================================

This library integrates with the excellent graphene library in a simple way: By providing a ScopedDjangoNode
class with default permission handling.

.. code-block:: python

    from django_scoped_permissions.graphql import ScopedDjangoNode

    class UserNode(ScopedDjangoNode):
        class Meta:
            # Note that interfaces = (Node,) is added automatically
            model = User

This default implementation here adds a custom permission guard on resolving of the node. If the model is
a ScopedModel, when resolving an object, its :code:`get_required_scopes` method is used to retrieve
the required scopes, and matches these against the callers :code:`get_granting_scopes`.


Custom node permissions
--------------------------------------

One can also customize the required scopes:

.. code-block:: python

    from django_scoped_permissions.graphql import ScopedDjangoNode

    class UserNode(ScopedDjangoNode):
        class Meta:
            model = User
            node_permissions = (
                "scope1:scope2",
            )


Now any user with scopes granting access to :code:`scope1:scope2` will be able to access any node.

You can also use variables in the permissions, to resolve context values or values/functions of the object:

.. code-block:: python

    from django_scoped_permissions.graphql import ScopedDjangoNode

    class UserNode(ScopedDjangoNode):
        class Meta:
            model = User
            node_permissions = (
                "company:{context.company.id}:user",
            )

The following special variables will be available in this context:

 * :code:`required_scopes`: The required scopes of the object being resolved.
 * :code:`user`: The calling user.


You can also use permission guards:

.. code-block:: python

    from django_scoped_permissions.graphql import ScopedDjangoNode

    class UserNode(ScopedDjangoNode):
        class Meta:
            model = User
            node_permissions = ScopedPermissionGuard(
                "company:{context.company.id}:user",
            ) | ScopedPermissionGuard(scope="user", verb="read")


Custom field permissions
------------------------------------

The class also provides a streamlined way to provide permissions for field resolvers easily:


.. code-block:: python

    from django_scoped_permissions.graphql import ScopedDjangoNode

    class UserNode(ScopedDjangoNode):
        class Meta:
            model = User
            field_permissions = {
                "weight": ("users:can-read-weight", "{required_scopes}:read-weight", )
            }

