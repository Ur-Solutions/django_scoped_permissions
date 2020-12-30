================
Core concepts
================

Throughout the section we're gonna use "organizations" and "users" as typical examples of models within your business domain. Hence we assume that in all the examples below, that there
exists a model `Organization` and a model `User`.

Permission strings and scopes
--------------------------------

The core concept of this library revoles around the notion of a *scoped permission string*. They (may) look like this:

.. code-block::

    read
    write
    update
    create
    user:1
    user:1:read
    organization:1
    organization:1:create
    =organization:1
    -organization:1
    organization:1:user:2

We say that each string delimited by a colon (:) defines a **permission scope**. We say that each subpart defined by a new colon of a permission defines a **parent scope** of the permission.

Take the permission :code:`organization:1:create`. Here :code:`organization`, :code:`organization:1` and :code:`organization:1:create` are the various scopes of the permission string. The two first are the parent scopes of the permission string.

While in many typical permission schemes permissions are matched exactly to ensure a grantee has the required access, in this library, permission strings are matched in a "cascading" manner on all parent scopes. We say that scopes are used in one of two contexts: As a **required permission** or as a **granting permission**.

Say for instance that you as a user have been granted a permission :code:`organization:1`. Then suppose you are trying to access a resource which requires the permission :code:`organization:1:setting:user`. Since you have the :code:`organization:1` permission, you will be given access to this, as you **have access to a higher level scope in the required full scoped permission string**.
In other words, the permission :code:`organization:1` as a granting permission grants access to :code:`organization:1:setting:user` as a required permission.

Similarily, a user with any of the following scoped permission strings would be given access to the resource:

* :code:`organization`
* :code:`organization:1`
* :code:`organization:1:settings`

Let's take some basic scope examples, and read very roughly what they would mean:

* :code:`organization`: Has/requires access to all organizations
* :code:`organization:1`: Has/requires access to organization with id 1.
* :code:`user:1`: Has/requires access to the user with id 1.
* :code:`organization:1:user:1`: Has/requires access to the user with id 1 within the organization with id 1.

Note that the exact interpretation of the permission strings are up to you within your own business domain.

Scopes and verbs
--------------------------

There are two parts of a scoped permission string, the **base** and the **verb**. The verb is optional. Some examples of typical permissions with verbs:

* :code:`read`
* :code:`user:create`
* :code:`user:1:update`
* :code:`organization:1:delete`

These permissions can roughly be read as

* Can read everything.
* Can create users.
* Can update user 1 **and any sub-resource of the user**.
* Can delete organization 1 and delete **and any sub-resource of the organization**.

Some examples of typical permissions without verbs:

* :code:`user`
* :code:`organization:1`
* :code:`organization:1:user`

These permissions can roughly be read as

* Has full access to all users.
* Has full access to the organization with id 1 **and any sub-resource**.
* Has full access to all users within the organization with id 1 **and any sub-resource of the users**.

Verbs are special when used in required permissions. Let's illustrate with two quick examples.

Example 1
_______________________
Say you have the permission :code:`user:1:read`. Now suppose you are trying to access a resource which requires :code:`user:1:settings:read`, where *read* is a verb.
Notably, the permission you have is **not** a parent scope of the required permission.

However, the permission internal mechanism will still match these two permissions,
as the verb will be attached recursively to each parent scope of your granting permission when trying to matching the permissions.

Other permissions which would have granted access in this scenario are the following:

* :code:`user:1:settings:read`
* :code:`user:1:settings`
* :code:`user:1`
* :code:`user:read`
* :code:`user`
* :code:`read`

From this example, we can see that creating a simple read-only user for all resources can be done by simply attaching the permission :code:`read`.

Again, this depends on how you structure your business logic, but shows some of the power of the library.

Example 2
______________________
Say you have the permission :code:`user:setting` and suppose you are trying to access a resource which requires :code:`user:1:setting`, where setting is not a verb.

Here, you will not get access, as again the permission you have is **not** a parent scope of the required permission.

From the above two examples, it should be clear that creating a superuser can be done with something akin to adding the following permissions: :code:`read`, :code:`update`, :code:`create`, :code:`delete`.

Exact permissions
-------------------------
One problem with the "cascading" property of the scoped permission system is that it may become hard to limit permissions "higher up" in the hierarchy. Suppose for instance that you want to grant a user access to read information about an organization without granting full read access to everything in the organization.

With the permission :code:`organization:1:read` we are likely to have the problem that the user automatically gets read-access to all resources within the organization. That is, if you model permission strings in a manner alike :code:`organization:1:user`, :code:`organization:5:vehicles`.

We can solve this problem by using an exact operator before the permission :code:`=organization:1:read`. This very roughly translates to "Has read access to organization 1, but no data within organization 1".
Exactly what this means semantically is up to you, but in terms of permission matching, this basically means that the required scope and the granting scope must match exactly (not including the "=").
To give an example, :code:`=organization:1` will **not** match :code:`organization:1:user`.

This can be used on any permission string:

* :code:`=organization:1:read`
* :code:`=organization:1`
* :code:`=user`

Exclusion permissions
-------------------------
Another problem we might have, is revoking specific permissions. Say for instance that you want a user by default to have access to all organizations, so the user has the permission :code:`organization`, but not to the organization with id 2.

We can achieve this with an **exclusion permission**: :code:`-organization:2`. In combination, these two permission yields access to all organizations apart from the organization with id 2.

Note that exclusion permissions always takes precedence over inclusion permissions.


Exact exclusion permissions
-------------------------------

We can combine the above two notions, e.g. `-=organization:2`. This will revoke access to exactly the permission `organization:2`.

Interestingly, this will still grant access to required permissions such as `organization:2:user`.


Final note
-------------------------------
Note that while a lot of the remaining part of the documentation will revolve aronud how to set up permissions
using the database, the library can be used fully statelessly.

The library's primary purpose is to provide helper methods and methodology for using the above schematics
to do permission matching. Hence it is fully possible to simply generate a scoped permissions on runtime,
and then match with required static or dynamic permissions.

This will be explored in a later chapter.
