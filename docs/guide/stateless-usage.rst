====================================
Stateless usage
====================================


One of the advantages of this library, is that in principle, permissions can be used more or less in a stateless manner.

To illustrate, suppose we have three user types: "normal", "moderator" and "administrator". Each of these user types
should yield a different set of permissions. If these should not vary between users, we can easily achieve what we
want by an appropriate implementation of :code:`get_required_scopes`.

.. code-block:: python

    from django_scoped_permissions.graphql import ScopedDjangoNode
    from django.utils.translation import _ as gettext_lazy

    class User(models.Model):
        class UserTypeChoices(models.TextChoices):
            NORMAL = "normal", _("Normal")
            MODERATOR = "moderator", _("Moderator")
            ADMINISTRATOR = "administrator", _("Administrator")

        ...
        organization = models.ForeignKey(Organization, on_delete=models.CASCADE) # Say every user is part of an organization
        user_type = models.CharField(max_length=16, choices=UserTypeChoices.choices, default=UserTypeChoices.NORMAL)


        def get_granting_scopes(self):
            scopes = []

            # Always grant access to oneself
            scopes.append(create_scope(User, self.id))

            if self.user_type == UserTypeChoices.NORMAL:
                # Has read access to your organization
                scopes.append(create_scope(Organization, self.organization.id, "read"))
            elif self.user_type == UserTypeChoices.MODERATOR:
                # Has read access to all other users
                scopes.append(create_scope(User, "read"))
                scopes.append(create_scope(Organization, self.organization.id, "read"))
            elif self.user_type == UserTypeChoices.ADMINISTRATOR:
                # Can do everything within an organization, can also create users
                scopes.append(
                    create_scope(Organization, self.organization.id, verb)
                    for verb in ["create", "update", "read", "delete"]
                )
                scopes.append(create_scope(User, "create"))

            return scopes


And this solution may in fact be sufficient for all our requirements. Typically, we've found that a powerful
:code:`get_granting_scopes` method often diminishes the need for a lot of persistent storage.

