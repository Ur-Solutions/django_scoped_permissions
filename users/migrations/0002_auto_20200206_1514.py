# Generated by Django 3.0.3 on 2020-02-06 15:14

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0002_company_users'),
        ('auth', '0011_update_proxy_permissions'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UserTypes',
            new_name='UserType',
        ),
    ]