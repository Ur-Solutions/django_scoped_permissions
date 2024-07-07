# New requirements

import graphene

## New create scope with verb separated

```py
sp("user", "1", verb="read")  # → "user:1@read"
sp("user", "1", "read")  # → "user:1:read"
sp(scope="user:1", verb="read")  # → "user:1@read"
```

## More clear core API

```python

check_scoped_permission(required_permission="user:1", granting_permission="user:1@read")  # True
check_scoped_permission(required_permissions=["user@read", "user:1@read"], granting_permission="user:1@read")  # True
check_scoped_permission(required_permissions=["user@read", "user:1@read"],
                        granting_permissions=["checklists:1@read", "user@read"])  # True

check_scoped_permission(required_permission="user:1@read",
                        granting_permissions=["checklists:1@read", "user@read"])  # True
```

## An empty verb is the same as not having a verb

```python
check_scoped_permission(required_permission="user:1@read", granting_permission="user:1@")  # True
check_scoped_permission(required_permission="user:1", granting_permission="user:1@")  # True
check_scoped_permission(required_permission="user:1@", granting_permission="user:1")  # True
```

## Some helpers are available for creating these

# "sp" results are ScopedPermissionTree objects and can easily be combined

```python
sp("user", "2", verb="write") & sp("user", "1", verb="read")  # → "user:1&user:2@write"
```

# Simpler API for protecting models without inheritance

```python
@protect_model(
"user:{self.id}",
)
class User(AbstractUser):
    pass
```

# The API auto-implements a method "check_access", which takes a ScopedPermissionProvider instance as the second

# argument and calls its "provides_permissions" method. This implementation looks like this:

```python
@protect_model(
"user:{self.id}@{verb}",
)
class User(AbstractUser):

    def check_access(self, provider: ScopedPermissionProviderLike, verb: Optional[str] = None):
        required_permission = []

        return check_scoped_permissions(provider.provides_permissions(), [f"user:{self.id}@{verb}"])

```

# In practice, the "user:{id}" part will be supplied by a method named "get_required_permissions". This can

# also be overridden to provide a different implementation. check_access can also be customised:

```python
class User(AbstractUser):
    def get_required_permissions(self, provider):
        return create_scoped_permission(f"user:{self.id}")

    def check_access(self, provider: ScopedPermissionProvider):
        if time.time() > self.last_accessed_at + 60:
            return True

        return check_scoped_permissions(provider.provides_permissions(),
                                        self.get_instance_required_permissions(provider))

```

# Simpler API for providing permissions per model. The simplest way to do this is to add the provides_permissions method.

# This will attach the StatelessScopedPermissionProvider to the model.

```python
@provides_scoped_permissions(
    "user:{self.id}",
)
class User(AbstractUser):
    pass
```

# What actually happens under the hood here is that the StatelessScopedPermissionProvider will be added, which has

# a method "provides_permissions" which returns the list of permissions specified:

@provides_scoped_permissions(
"user:{self.id}",
)
class User(AbstractUser, StatelessScopedPermissionProvider):

    def provides_permissions(self):
        return [f"user:{self.id}"]

# The stateful version can also be used, if you want the models to store permissions in the database:

class User(AbstractUser, ScopedPermissionProvider):

    def provides_permissions(self):
        return super().provides_permissions()

# If you have other related models that should be used to get permissions, you can supply this in the

# provides_scoped_permissions decorators:

@provides_scoped_permissions(
related_scope_providers=[
{
"model": "UserType",
"field": "user_types",
}
],
stateful=True
)
class User(AbstractUser):
pass

# You can also implement it more directly

class User(AbstractUser, ScopedPermissionProvider):
def provides_permissions(self):
user_types = self.user_types.all()
permissions_from_user_types = [

        ]

        for user_type in user_types:
            permissions_from_user_types.append(user_type.provides_permissions())

        return permissions_from_user_types + super().provides_permissions()

# If you want a mix of stateful and stateless permissions, you can use the following pattern:

class User(AbstractUser, ScopedPermissionProvider):

    def provides_permissions(self):
        permissions_from_database = super().provides_permissions()

        return [f"user:{self.id}"] + permissions_from_database

# Better decorators

```python
@protect_view("user:1@read")
def some_function(request):
    pass
```

```python
@protect_view(scope="{request.organization.id}", verb="read")
def some_function(request):
    pass
```

@protect_view(
"organization:{context.organization.id}@read|user:1@read"
)
def some_function(request):
pass

@protect_view(
"users:{user_id}@read",
)
def some_function(request, user_id):
pass

# These variants will all by default wrap the data in a guard, and then check

# Views can also be protected by a function

def has_user_read_access(request, user_id):
calling_user = request.user

    if not calling_user.is_authenticated:
        return False

    return check_scoped_permission(required_permission=f"user:{user_id}@read", granting_permissions=[f"user:{user_id}"])

```python
@protect_view(
    fn=has_user_read_access,
)
def some_view(request, user_id):
    pass
```

# Integrations with graphene/graphene-django

class Queries(graphene.ObjectType):
user = graphene.Field(UserNode)

    @protect_field(
        "user:{user.id}@read"
    )
    def resolve_user(self, info):
        return User.objects.get(pk=1)

## This case will attach a permission check to the get_node method of the DjangoObjectType

@protect_django_object_type(
"user:{user.id}@read"
)
class UserNode(DjangoObjectType):
class Meta:
model = User

# We can also easily protect mutations.

@protect_mutation(
"user:{user.id}@update"
)
class ChangeUserMutation(graphene.Mutation):
class Arguments:
id = graphene.ID(required=True)
name = graphene.String(required=True)

    user = graphene.Field(UserNode)

    ## This method will automatically be wrapped in a permission check
    def mutate(self, info, id, namw):
        user = Users.objects.get(pk=id)
        user.name = name

        user.save()

        return ChangeUserMutation(user=user)

## Finally, we can easily protect multiple fields on a single objecttype.

```python
@protect_object_type(
    fields={
        "user": "user:{input.id}@read",
        "all_users": "user@read"
    }
)
class UserQuery(graphene.ObjectType):
    user = graphene.Field(UserNode, id=graphene.ID(required=True))
    all_users = DjangoListField(UserNode)

    ### We can still implement custom resolvers, and they will be protected
    def resolve_all_users(self, info):
        return User.objects.all()

    ### We can also override permissions on a per-field basis
    @protect_field(
        "user:{input.id}@change"
    )
    def resolve_user(self, info, id):
        return User.objects.get(pk=id)

```
## "context" is named "request" to adhere with the functional method API

@protect_field(
"user:{request.user.id}@read"
)
def resolve_me(self, info):
return User.objects.get(pk=info.context.user.id)

# Creating reusable permissions is now easier.

can_view_other_users = create_scoped_permission("user@read")
can_delete_other_users = create_scoped_permission("user@delete")
can_invite_users = create_scoped_permission("user@invite")

## These can now be used both in guards and in providers

@provides_scoped_permissions(
stateful=True,
)
class User(AbstractUser):

    def provides_permissions(self):
        permissions = []

        permissions.append(can_view_other_users)

        if self.user_type == UserType.ADMIN:
            permissions.append(can_delete_other_users)
            permissions.append(can_invite_users)

        permissions_from_database = super().provides_permissions()
        return permissions + permissions_from_database

# A simple API for flattening permissions

```python
def flatten_permissions(permissions: Iterable[str]) -> Iterable[str]:
    pass

flatten_permissions(["user:1", "user:1@read"])  # → ["user:1"], since user:1@read is dominated always
flatten_permissions(["user:1", "user:1@read", "user:2@update"])  # → ["user:1", "user:2@update"]
flatten_permissions(["@read", "user:1@read", "checklists:2@read"])  # → ["read"]
```

# All methods accept a "resolve_context" argument. By default, the context is set to some sensible default, taking

# primarily the function arguments as input. This can be overridden. Examples:

```python
@protect_view(
    "user:{user.id}@read",
    resolve_context=lambda request: {"user": request.user}
)
def some_function(request, user):
    pass
```

# You can resolve custom model instances directly in this context:

```python
@protect_view(
    "user:{user.id}@read",
    resolve_context=lambda request, id: {"user": Users.objects.get(pk=id)}
)
def some_function(request, user_id):
    pass
```

### You can also disambiguate ids in this manner

```python
@protect_view(
    "user:{id}@read",
    resolve_context=lambda request, id: {"id": disambiguate_id(id)}
)
def some_function(request, user_id):
    pass
```

There is also a helper for the specific case of disambiguating ids in the context:

```python
@protect_view(
    "user:{id}@{verb}",
    resolve_context=resolve_disambiguated_ids_to_context(["id"], then=lambda request, id: {"verb": "run"}),
)
def some_function(request, user_id):
    pass
```

It accepts a parameter "then", which is a function that takes the request and the disambiguated id, and returns a dictionary.

The context will be merged into the default context. This can be used to resolve custom model instances directly in this context.

## Strict mode

In strict mode, if some context argument is not supplied, an exception will be thrown and the view will be protected.

You can enable strict mode in the django settings. It is enabled by default.

DJANGO_SCOPED_PERMISSIONS_STRICT_MODE = True


