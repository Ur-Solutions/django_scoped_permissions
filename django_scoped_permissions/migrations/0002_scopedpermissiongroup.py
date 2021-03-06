# Generated by Django 3.0.6 on 2020-12-19 22:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_scoped_permissions', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ScopedPermissionGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField()),
                ('scoped_permissions', models.ManyToManyField(blank=True, related_name='in_groups', to='django_scoped_permissions.ScopedPermission')),
            ],
        ),
    ]
