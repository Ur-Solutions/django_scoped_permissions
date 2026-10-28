# Django scoped permissions

Scoped permissions for Django models and Graphene mutations.

## Compatibility

The test matrix covers Python 3.12 with Django 5.2, 6.0 and 6.1,
Graphene Django 3, Graphene Django CUD 0.13, and factory_boy 2.12 and 3.
factory_boy is a development dependency; installing this library does not
constrain an application's factory_boy version.

Pydash 4 through 8 is accepted. Prefer a current version for new applications:
Pydash 4 imports `pkg_resources`, which requires an older setuptools release
(for example, 80.9.0). The default lock uses Pydash 8.

## Development

Install the tools pinned in `mise.toml`, then run:

```sh
mise install
mise exec -- poetry install
mise exec -- make test
mise exec -- poetry run python manage.py makemigrations --check --dry-run
mise exec -- make build
```

The default tests use SQLite. CI also defines PostgreSQL and SQL Server jobs.
For a disposable local database, install the appropriate Django backend and set
`SCOPED_TEST_DATABASE` to `postgresql` or `mssql`, plus
`SCOPED_TEST_PASSWORD`. Optional settings are `SCOPED_TEST_HOST`,
`SCOPED_TEST_PORT` and `SCOPED_TEST_USER`. The test runner creates and drops
`test_scoped_permissions`. SQL Server requires ODBC Driver 18.

## Mist branch lineage

This update builds on the `mist` branch at `b6bd54a`, including its SQL Server
schema changes and batch/filter mutation wrappers. Mist currently pins that
commit rather than using a published release. Those changes must be included
in a shared release before Mist can switch to it.
The current `master` branch also contains unfinished 0.2 model/API changes;
switching Mist directly to it is not a compatible upgrade.

The SQL Server change removed the unique constraint on the scope text field
from the original migration. Existing databases created from the older
`develop` migration may still have that constraint. This update leaves that
historical behavior unchanged; reconciling those database schemas remains
necessary before consolidating the branches into a shared release.
