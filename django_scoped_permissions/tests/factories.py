import factory
from factory.fuzzy import FuzzyInteger
from django.db import models
from .models import Company, User, Pet, Building
from django_scoped_permissions.util import create_scope


class CompanyFactory(factory.DjangoModelFactory):
    class Meta:
        model = Company

    name = factory.Sequence(lambda n: "company%s" % n)
    short_name = factory.Sequence(lambda n: n)

    email = factory.Faker("email")


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Sequence(lambda n: "username%d" % n)
    email = factory.Sequence(lambda n: "%d@urtesting.sexy" % n)


class PetFactory(factory.DjangoModelFactory):
    class Meta:
        model = Pet

    name = factory.Faker("first_name")
    age = FuzzyInteger(0, 42)

    user = factory.SubFactory(UserFactory)


class BuildingFactory(factory.DjangoModelFactory):
    class Meta:
        model = Building

    name = factory.Faker("catch_phrase")
    company = factory.SubFactory(CompanyFactory)

    created_by = factory.SubFactory(UserFactory)
