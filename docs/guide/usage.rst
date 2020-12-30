================================
Basic usage
================================

Basic scope matching
-------------------------------

There are a number of core methods in the library which is used to perform the primary matching of permissions in
accordance with the previous section. The most important of these is the :code:`scope_grants_permission`
and :code:`scopes_grant_permissions` methods.

.. code-block:: python

    from django_scoped_permissions.core import scope_grants_permission, scopes_grant_permissions

    # First argument is required scope, second is granting scope.
    scope_grants_permission("scope1:scope2", "scope1")  # True
    scope_grants_permission("scope1:scope2", "=scope1")  # False
    scope_grants_permission("scope1", "-scope1")  # False
    scope_grants_permission("scope1:scope2", "scope3:edit")  # False

    # First argument is required scopes, second is granting scopes. Note that the method
    # returns true if _any_ matches. Also note that any excluding permission takes precedence.
    scopes_grants_permissions(["scope1:scope2"], ["scope1"])  # True
    scopes_grants_permissions(["scope1:scope2"], ["=scope1", "scope1"])  # True
    scopes_grants_permissions(["scope1:scope2"], ["-scope1", "scope1:scope2"])  # False

These methods also accepts a third argument for the required `verb`.


.. code-block:: python

    from django_scoped_permissions.core import scope_grants_permission, scopes_grant_permissions

    scope_grants_permission("scope1:scope2", "scope1:read", "read")  # True
    scope_grants_permission("scope1:scope2", "scope1", "read")  # True
    scope_grants_permission("scope1:scope2", "scope1:scope2:read", "read")  # True
    scope_grants_permission("scope1:scope2", "scope1:scope2:update", "read")  # False

    scopes_grants_permissions(["scope1:scope2"], ["scope1", "scope1:read"], "read") # True
    scopes_grants_permissions(["scope1:read", "scope3:update"], ["scope3", "=scope1:read"], "read") # True
    # Note here that since we have a direct exclude on scope3:update, the request is disallowed.
    scopes_grants_permissions(["scope1:read", "scope3:update"], ["-scope3:update", "=scope1:read"], "read") # False


Under the hood, these methods use the :code:`scope_matches` method, which simply makes a required scope with a granting scope.
Note that while it handles exact matches properly, it does not handling excluding scopes properly. This is done in the above methods.
It is like a light-weight :code:`scope_grants_permission` which does not handle exclude permission nor verbs. It should rarely be used directly.

Another important helper-method is :code:`create_scope`. It simply concatenates objects and strings to create a scoped permission string.
Since creating scoped strings is a major part of using this library, making the code as readable as possible is important.
The method also adds some magic which allows us to pass in model instances and model classes, which will automatically have
their (associated model) names extracted:

.. code-block:: python

    from django_scoped_permissions.core import create_scope
    from users.models import User # hypothetical user model
    from forum.models import Thread # hypothetical forum thread model

    create_scope("scope1", "scope2") # → "scope1:scope2"
    create_scope(*["scope1", "scope2", "scope3", "scope4"]) # → "scope1:scope2:scope3:scope4"
    create_scope(User, 1) # → "user:1"

    forum_thread = ForumThread.objects.get(pk=1337)
    create_scope(forum_thread, forum_thread.id, "read") # → "thread:1337:read"


Models and Mixins
-------------------------------

There are four models of importance in the library: :code:`ScopedPermission`, :code:`ScopedPermissionGroup`, :code:`ScopedModel` and :code:`ScopedPermissionHolder`.


ScopedPermission
______________________

Simply a model which persists a scoped permission with *exact* and *exclude* parameters.

ScopedPermissionGroup
__________________________

A model which has a name, and a m2m-field to :code:`ScopedPermission`. I.e. it contains a number of scoped permissions
under a group name. This can be useful in scenarios where you want to create reusable sets of permissions.


ScopedModel
_______________________________

A Model inheriting from ScopedModel is a model which provides two methods: :code:`get_required_scopes` and :code:`has_permission`.
The model is based in the mixin ScopedModelMixin, and simply inherits from Django's :code:`models.Model` as well.

:code:`get_required_scopes` should be implemented by every model inherited from ScopedModel, and should return all
scopes which on a match will grant access to **an object of the model**.

Here is an example from a real-life application (simplified for brevity):

.. code-block:: python

    # forum.models

    from django_scoped_permissions.models import ScopedModel

    class Thread(ScopedModel):
        organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
        title = models.TextField()

        created_at = models.DateTimeField(auto_now_add=True)

        def get_required_scopes(self):
            return [
                create_scope(self, self.id),   # thread:{self.id}
                create_scope(Organization, self.organization.id, self, self.id) # organization:{organization.id}:thread:{self.id}
            ]


    class Post(ScopedModel):
        thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
        content = models.TextField()

        created_at = models.DateTimeField(auto_now_add=True)

        def get_required_scopes(self):
            return [
                # You get the idea
                create_scope(self, self.id),
                create_scope(self.thread, self.thread.id, self, self.id)
                create_scope(Organization, self.organization.id, self.thread, self.thread.id, self, self.id)
            ]

So the point here is the following:

 1. We typically want the objects to be accessible directly when a calling user has a direct matching permission, e.g. "thread" or "thread:1"
 2. But also when the user has permission to an object higher up in your data hierarchy, e.g. "organization" or "organization:1".

Exactly how you structure this is completely up to you, and depends a lot on your use-case and your data.
If in the above example, say, we didn't want a post to be accessible just because a user has access to a thread, we would remove the second entry under :code:`Post.get_required_scopes`.

:code:`get_required_scopes` should return a list.

The second method :code:`has_permission` has a much more opinionated implementation, and should not be overriden unless
you know what you are doing. It takes as argument a ScopedPermissionHolderMixin instance and an optional action, and
checks whether the instance has access to the current object, as defined per the :code:`get_required_scopes` method.

ScopedModel is inherently stateless, and adds no extra database-bloat to your model.

ScopedPermissionHolder
_______________________________

ScopedPermissionHolder is an abstract model used on the models you want to be able to hold permissions that grants access.
It does two important things:

 1. Adds m2m database fields to both :code:`ScopedPermission` and :code:`ScopedPermissionGroup`.
 2. Implements the four permission methods of ScopedPermissionHolderMixin.

The four methods mentioned are :code:`get_granting_scopes`,:code:`has_scoped_permissions`,
:code:`has_any_scoped_permissions`, :code:`has_all_scoped_permissions`.

Note that :code:`has_scoped_permissions` is just an alias for :code:`has_any_scoped_permissions` by default. There is
nothing wrong with overriding this default behaviour, however. :code:`has_scoped_permissions` is the method which will
typically be used by the library internally.

:code:`get_granting_scopes` is the method of most interest here. It returns all the scopes the holder has permission to.
The default implementation of this simply fetches all the scopes in the database, both directly associated to the holder,
but also via the holder's ScopedPermissionGroups. This default implementation "hides" in a property called :code:`resolved_scopes`.

Very typically you are going to override this default implementation (by expanding on it). A typical example is a
User model, which will always have access to their own resources:

.. code-block:: python

    class User(AbstractUser, ScopedPermissionHolder):

        # ...

        def get_granting_scopes(self):
            super_scopes = super().get_granting_scopes()

            return super_scopes + [create_scope(self, self.id)]

:code:`get_granting_scopes` should return a list.

The ScopedPermissionHolder model implements the ScopedPermissionHolderMixin class, which simply provides stubs for the
four methods mentioned aboce.

Finally, :code:`ScopedPermissionHolder` has a handy utility function :code:`add_or_create_permission` which simply
creates a scoped permission object in the database (or retrieves one if it exists), and adds it to the holder.

Common recipes
-------------------------------

User with User Types/ Groups
_________________________________

If you want user types with permission, you probably want the user to automatically inherit all permissions.

.. code-block:: python


    class UserType(ScopedPermissionHolder):
        name = models.TextField()

    class User(AbstractUser, ScopedPermissionHolder):

        user_types = models.ManyToManyField(UserType, blank=True)

        def get_granting_scopes(self):
            user_scopes = super().get_granting_scopes() + [create_scope(self, self.id)]

            user_type_scopes = [
                scope for user_type in self.user_types.all() for scope in user_type.get_granting_scopes()
            ]

            # We might want to delete duplicates here
            return list(set(user_scopes + user_type_scopes))


Permission with placholders
__________________________________________

There are no rules regarding what you can put in a scoped permission string. Which means you can also put placeholders
which resolve at runtime. A typical usecase here would be a permission which has a placeholder for say an organization
id which is resolved on runtime.

Here we also use another utility function which expands a scope permission string based on context values.

.. code-block:: python

    class User(AbstractUser, ScopedPermissionHolder):

        def get_granting_scopes(self):
            user_scopes = super().get_granting_scopes() + [create_scope(self, self.id)]

            organization_ids = [organization.id for organization in self.organizations.all()]
            expanded_scopes = expand_scopes_from_context(user_scopes, {"organization": organization_ids})

            return expanded_scopes

    class Organization(ScopedPermissionModel):
        name = models.TextField()
        users = models.ManyToManyField(User, on_delete=models.CASCADE, related_name="organizations")


    user = User.objects.get(pk=1)
    user.add_or_create_permission("organization:{organization}:read")  # Add read permission to all organizations the user is a member of
    organization_1 = Organization.objects.create(name="org1")
    organization_2 = Organization.objects.create(name="org2")

    user.organizations.add(organization_1)
    user.organizations.add(organization_2)

    print(user.get_granting_scopes())  # Prints ["organization:1:read", "organization:2:read", "user:1"]


Superusers
__________________________________________

There is no explicit superuser-handling in the library. This is intentional, as some applications of the library might
not want such functionality. The easiest way to get superuser-functionality currently, is to do one of two things:

 1. Make sure superusers have all relevant top-level verbs (e.g. create, read, update, delete, or which ever verbs you use).
 2. Create two new abstract model which inherits from ScopedPermissionModel and ScopedPermissionHolder, and override
    the methods :code:`ScopedPermissionModel.has_permission` and :code:`ScopedPermissionHolder.has_scoped_permissions`.

When we implement wildcards (on the roadmap), this becomes a tad easier.
