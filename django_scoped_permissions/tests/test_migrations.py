import pytest
from django.db import IntegrityError, connections, transaction
from django.db.migrations.executor import MigrationExecutor
from django.db.migrations.exceptions import IrreversibleError


APP = "django_scoped_permissions"
PREVIOUS = (APP, "0002_scopedpermissiongroup")
CURRENT = (APP, "0003_stored_scoped_permission")


@pytest.fixture
def migration_database(django_db_blocker):
    """Exercise historical schemas without changing the suite's test database."""
    alias = "permission_migration_test"
    connections.databases[alias] = {
        **connections["default"].settings_dict,
        "NAME": ":memory:",
    }
    with django_db_blocker.unblock():
        connection = connections[alias]
        try:
            executor = MigrationExecutor(connection)
            executor.migrate([PREVIOUS])
            apps = executor.loader.project_state([PREVIOUS]).apps
            yield connection, apps
        finally:
            # Django's SQLite wrapper deliberately ignores close() for in-memory
            # databases; this disposable connection must actually be released.
            if connection.connection is not None:
                connection.connection.close()
            del connections[alias]
            del connections.databases[alias]


def test_permission_migration_preserves_rows_and_flags(migration_database):
    connection, old_apps = migration_database
    old_permission = old_apps.get_model(APP, "ScopedPermission")
    expected = []
    for exact, exclude in [(False, False), (True, False), (False, True), (True, True)]:
        permission = old_permission.objects.using(connection.alias).create(
            scope="company:42", exact=exact, exclude=exclude
        )
        expected.append((permission.pk, "company:42", None, exclude, exact))

    executor = MigrationExecutor(connection)
    executor.migrate([CURRENT])
    apps = executor.loader.project_state([CURRENT]).apps
    permission = apps.get_model(APP, "StoredScopedPermission")
    assert list(
        permission.objects.using(connection.alias).order_by("pk").values_list(
            "pk", "scope", "verb", "is_negation", "is_exact"
        )
    ) == expected
    tables = connection.introspection.table_names()
    assert "django_scoped_permissions_scopedpermission" not in tables
    assert "django_scoped_permissions_scopedpermissiongroup" not in tables
    assert "django_scoped_permissions_scopedpermissiongroup_scoped_permissions" not in tables


def test_permission_migration_supports_distinct_verbs_and_rejects_duplicates(migration_database):
    connection, _ = migration_database
    executor = MigrationExecutor(connection)
    executor.migrate([CURRENT])
    permission = executor.loader.project_state([CURRENT]).apps.get_model(
        APP, "StoredScopedPermission"
    )
    permissions = permission.objects.using(connection.alias)
    permissions.create(scope="company:42", verb="read")
    permissions.create(scope="company:42", verb="update")
    with pytest.raises(IntegrityError), transaction.atomic(using=connection.alias):
        permissions.create(scope="company:42", verb="read")
    assert permissions.count() == 2

    with pytest.raises(IrreversibleError):
        MigrationExecutor(connection).migrate([PREVIOUS])
    assert set(permissions.values_list("verb", flat=True)) == {"read", "update"}


def test_permission_migration_refuses_to_discard_groups(migration_database):
    connection, old_apps = migration_database
    permission = old_apps.get_model(APP, "ScopedPermission").objects.using(
        connection.alias
    ).create(scope="company:42", exclude=True)
    group_model = old_apps.get_model(APP, "ScopedPermissionGroup")
    group = group_model.objects.using(connection.alias).create(name="Managers")
    group.scoped_permissions.add(permission)

    with pytest.raises(RuntimeError, match="Migrate legacy permission groups"):
        MigrationExecutor(connection).migrate([CURRENT])

    assert group_model.objects.using(connection.alias).get(pk=group.pk).name == "Managers"
    assert list(group.scoped_permissions.values_list("pk", flat=True)) == [permission.pk]
