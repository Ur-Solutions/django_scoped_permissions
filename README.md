# Django Scoped Permissions

This branch contains the in-progress 0.2 implementation, including
`StoredScopedPermission`, separate verbs and the permission parser/tree API.
The `mist` branch has a different model and SQL Server migration history;
the two branches are maintained independently.

## Compatibility work

The dependency ranges target Django 5.2, 6.0 and 6.1, with factory_boy 2.12
and 3.x as development dependencies only. Python 3.12+ is required: the
existing parser already uses Python 3.12's `type` statement. The `lark`
dependency and Pydash 8 requirement are retained on this branch.

**This branch is not ready for a release.** Compatibility validation is
blocked by the unfinished 0.2 migration:

- The test app has no initial migration, so database setup fails.
- Package migrations still create `ScopedPermission` and
  `ScopedPermissionGroup`, while the models define `StoredScopedPermission`.
- Some model tests still use `exact`/`exclude` and string permissions,
  rather than the new model fields and permission objects.

These changes preserve the current model, parser and migration history.
Finishing the 0.2 migration and its semantics is required before claiming
full compatibility. CI keeps the complete test suite and migration check
as failing gates until that work is completed; it does not skip these tests.

## Development

Tool versions are pinned in `mise.toml`. Install them with `mise install`,
then use:

```sh
mise exec -- poetry install
mise exec -- make test-cov
mise exec -- poetry run python manage.py makemigrations --check --dry-run --noinput
mise exec -- make build
mise exec -- poetry run twine check dist/*
```

CI tests each Django/factory_boy combination independently on SQLite.
`.DS_Store` files are ignored.
