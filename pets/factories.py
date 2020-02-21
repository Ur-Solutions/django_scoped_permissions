import factory

from pets.models import Pet
from users.factories import UserFactory


class PetFactory(factory.DjangoModelFactory):
    class Meta:
        model = Pet

    user = factory.SubFactory(UserFactory)
    name = "Pet"
    age = 13
