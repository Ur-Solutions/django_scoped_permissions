# Generated by Django 3.0.3 on 2020-02-06 16:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('permissions', '0001_initial'),
        ('users', '0003_usertype_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='usertype',
            name='scoped_permissions',
            field=models.ManyToManyField(blank=True, to='permissions.ScopedPermission'),
        ),
    ]