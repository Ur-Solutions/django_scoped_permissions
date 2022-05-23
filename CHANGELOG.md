
# Changelog

## Version 0.1.7
* Add pydash as peer dependency

## Version 0.1.6
* (graphql): Fix a bug related to field permissions
* Bump graphene-django get_queryset calls to use new signature

## Version 0.1.5
* (models): Fix a bug for Django 3.2 where the resolve methods would crash due to an output_field not being explicitly set on an annotation query.

## Version 0.1.4
* (graphql): Add missing context variable in CreateMutation
* (guards): Change default behaviour to be "True". Is now overrideable

## Version 0.1.3
* (core): Implement wildcards

## Version 0.1.2
* (guards): Fix bug when passing empty list to ScopedPermissionGuard

## Version 0.1.1
* (graphql): Fix bad get_permission handling and add missing guard contexs

## Version 0.1.0

* (core): Renamed action → verb
* (core): scopes_grant_permissions now returns True if required_scopes is empty.
* (docs): Add remaining documentation
* (guards): Introduce new guard system
* (graphql): ScopedDjangoNode checks permission with a "read" verb by default
* (graphql): All mutations use the new guard system
* (decorators): Now support and uses new guard system

## Version 0.0.9
* Fix bug with decorators context

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
