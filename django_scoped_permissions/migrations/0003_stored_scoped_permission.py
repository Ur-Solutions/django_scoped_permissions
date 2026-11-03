from django.db import migrations, models


def require_empty_legacy_groups(apps, schema_editor):
    group = apps.get_model("django_scoped_permissions", "ScopedPermissionGroup")
    if group.objects.using(schema_editor.connection.alias).exists():
        raise RuntimeError(
            "Migrate legacy permission groups and their assignments to your "
            "application's permission holders, then remove the legacy groups "
            "before applying django_scoped_permissions.0003."
        )


class Migration(migrations.Migration):
    dependencies = [
        ("django_scoped_permissions", "0002_scopedpermissiongroup"),
    ]

    operations = [
        # There is no replacement for groups in the current model. Refuse to
        # discard them. No reverse migration can preserve newly assigned verbs.
        migrations.RunPython(require_empty_legacy_groups),
        migrations.RenameModel(
            old_name="ScopedPermission", new_name="StoredScopedPermission"
        ),
        migrations.AlterUniqueTogether(
            name="storedscopedpermission", unique_together=set()
        ),
        migrations.RenameField(
            model_name="storedscopedpermission", old_name="exclude", new_name="is_negation"
        ),
        migrations.RenameField(
            model_name="storedscopedpermission", old_name="exact", new_name="is_exact"
        ),
        migrations.AddField(
            model_name="storedscopedpermission",
            name="verb",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="storedscopedpermission",
            name="is_negation",
            field=models.BooleanField(
                default=False,
                help_text="Whether this should be a negation, meaning that if scope is 'user:update' and is_negation is True then users with this usertype will not be able to update users, even their own.",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="storedscopedpermission",
            unique_together={("scope", "verb", "is_negation", "is_exact")},
        ),
        migrations.DeleteModel(name="ScopedPermissionGroup"),
    ]
