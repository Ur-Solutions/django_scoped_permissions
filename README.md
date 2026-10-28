# Django Scoped Permissions

Scope-based authorization for Django applications. Permissions describe access
to resources in a hierarchy, with optional verbs for actions such as reading
or updating a resource.

## Permission model

A permission combines a colon-separated scope, such as `company:42:project:7`,
with an optional verb, such as `read`. Exact-match and negation flags express
more specific access rules.

- `StoredScopedPermission` stores scopes, verbs, and matching flags in Django.
- Permission holders collect granted scopes; scoped models describe the
  permissions required to access their resources.
- Permission objects, guards, and the parser/tree API represent and evaluate
  access requirements.
- View and field decorators and Graphene-Django integrations apply permission
  checks at application boundaries.

## Compatibility

CI covers these Python and Django combinations:

| Django | Python 3.12 | Python 3.13 | Python 3.14 |
| --- | --- | --- | --- |
| 5.2 LTS | CI | CI | CI |
| 6.0 | CI | CI | CI |
| 6.1 | CI | CI | CI |

Each job selects the latest patch release in its Python and Django series and
runs the permissions tests, GraphQL integration tests, and migration checks
on SQLite. Package metadata is limited to these Python and Django series.

## Development

Install the tools pinned in `mise.toml` with `mise install`, then run:

```sh
mise exec -- poetry install
mise exec -- make test-cov
mise exec -- poetry run python manage.py makemigrations --check --dry-run --noinput
mise exec -- make build
mise exec -- poetry run twine check dist/*
```
