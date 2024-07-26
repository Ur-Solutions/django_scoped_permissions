import types

from factory import Faker, Sequence, SubFactory, post_generation
from factory.django import DjangoModelFactory
from faker import factory

from django_scoped_permissions.core.scoped_permission import sp
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

class UserWithScopedPermissionsFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda n: "scopedpermissionsusername%d" % n)
    email = Sequence(lambda n: "scopedpermissions@email%d" % n)

    @post_generation
    def scoped_permissions(self: User, create, extracted, **kwargs):
        if not create:
            return

        if not extracted:
            return

        permissions = [sp(perm) for perm in extracted]

        def get_granting_permissions(self, context=None):
            return permissions

        self.get_granting_permissions = types.MethodType(get_granting_permissions, self)
