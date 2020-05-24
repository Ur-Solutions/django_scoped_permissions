import factory

from django_scoped_permissions.tests.models import User, Pet


class UserFactory(factory.DjangoModelFactory):
    class Meta:
        model = User

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    username = factory.Sequence(lambda n: "username%d" % n)
    email = factory.Sequence(lambda n: "user-%d@ursolutions.no" % n)


class PetFactory(factory.DjangoModelFactory):
    class Meta:
        model = Pet

    user = factory.SubFactory(UserFactory)
    name = "Pet"
    age = 10
