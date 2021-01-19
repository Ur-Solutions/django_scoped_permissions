
# Changelog

## Version 0.0.8
* Fix bad graphene-django-cud pin

## Version 0.0.7
* (docs): Add documentation
* Improve core
	- Improve primary match-checking method `scope_matches`, it should now
	correctly match substrings.
	- Add `scope_grants_permission` method for singular permission matching.
	- Fix some formatting
	- Add tests
* (core): Update `expand_scopes`, change return pattern to Iterable
* (models): Rename HasScopedPermissionMixin → ScopedPermissionHolder
	- Instances of the class are now referred to as "holders".
* (models): Add ScopedPermissionGroupModel model and add to ScopedPermissionHolder as m2m-field.
* (models): Add `add_or_create_permission` method on ScopedPermissionHolder.
* (graphql): Add context resolution to decorators.
* (dev): Add pytest-testmon as dev dependency for watchable tests.
* BREAKING (models): Deprecate `get_scopes` and `get_base_scopes`. Rename to `get_granting_scopes` and `get_required_scopes`.
* BREAKING: Rename file `graphql_util.py` → `util.py`


## Version 0.0.6
* (Graphql): Fix an issue with bad permission checks

## Version 0.0.5
* Fix an issue with permissions not being spread properly

## Version 0.0.4
* Fix some issues with the graphene-django-cud classes

## Version 0.0.3
* Register ScopedPermission to admin site

## Version 0.0.2
* First useable release
* Adds graphene-django and graphene-django-cud integrations
* Simply API a bit

## Version 0.0.1
* Initial version, some basic structure
