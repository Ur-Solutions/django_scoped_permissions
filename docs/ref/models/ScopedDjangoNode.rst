.. _ScopedDjangoNode:

================================
ScopedDjangoNode
================================

A wrapper for DjangoObjectType which automatically adds permission handling to the node.

All meta arguments:

+--------------------------+------------+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| Argument                 | type       | Default   | Description                                                                                                                                                                       |
+==========================+============+===========+===================================================================================================================================================================================+
| model                    | Model      | None      | The model. **Required**.                                                                                                                                                          |
+--------------------------+------------+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| node_permissions         | Iterable   | None      | The permissions required to access the node. If not supplied, the models "get_base_scopes" method will be used to populate this field.                                            |
+--------------------------+------------+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| field_permissions        | Dict       | None      | A dictionary of permissions per field of the model used to check if the calling user has access to the field.                                                                     |
+--------------------------+------------+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+
| allow_anonymous          | Boolean    | False     | If true, the node can be accessed by an anonymous user.                                                                                                                           |
+--------------------------+------------+-----------+-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+


.. code-block:: python

    class User(HasScopedPermissionsMixin, AbstractUser, ScopedModel):
        secret_field = models.TextField()

        def get_base_scopes(self):
            return [create_scope(self, self.id)]  # E.g. "user:1"


    class UserNode(ScopedDjangoNode):
        class Meta:
            model = User
            allow_anonymous = False

    # Example with more restrictive permissions
    class RestrictiveUserNode(DjangoScopedNode):
        class Meta:
            model = User
            node_permissions = ["user"]  # Requires all permissions to all users
            field_permissions = {
                "secret_field": ["user:secret_field"]
            }

