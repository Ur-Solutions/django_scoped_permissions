================
Installation
================

Installation is done with pip (or via wrappers such as pipenv or poetry):

.. code:: bash

    pip install django_scoped_permissions


Make sure to add django_scoped_permissions to your INSTALLED_APPS:

.. code:: python

    INSTALLED_APPS = [
        # ...
        "django_scoped_permissions"
        # ...
    ]
    