===============================================
Django Scoped Permissions
===============================================

Django Scoped Permissions is a custom permission system Django. The core concept of the system is a "scope", which is very loosely defined as a string followed by a colon. A scoped permission
is a string containing one or more scopes, defining a permission hierarchy.

Such a scoped permission typically follows the natural hierarchy of your business domain.

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   guide/install
   guide/core-concepts
   guide/usage
   guide/guards
   guide/decorators
   guide/graphene-integration
   guide/graphene-django-cud-integration
   guide/stateless-usage

.. toctree::
   :maxdepth: 2
   :caption: Reference

   ref/models/index
