from factory import Faker, Sequence, SubFactory
from factory.django import DjangoModelFactory
from faker import factory

from django_scoped_permissions.tests.models import User, Pet, Company


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    first_name = Faker("first_name")
    last_name = Faker("last_name")
    username = Sequence(lambda n: "username%d" % n)
    email = Sequence(lambda n: "user-%d@ursolutions.no" % n)


class PetFactory(DjangoModelFactory):
    class Meta:
        model = Pet

    user = SubFactory(UserFactory)
    name = "Pet"
    age = 10


class CompanyFactory(DjangoModelFactory):
    class Meta:
        model = Company

    short_name = Sequence(lambda n: "company%d" % n)