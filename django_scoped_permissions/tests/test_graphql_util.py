from django.test import TestCase

from django_scoped_permissions.util import expand_scopes, expand_scopes_from_context


class TestExpandScopes(TestCase):
    def test__no_expansions__return_scopes(self):
        scopes = ["some:scope", "another:scope"]

        self.assertListEqual(scopes, list(expand_scopes(scopes)))
        self.assertListEqual(scopes, list(expand_scopes(scopes, {})))

    def test__single_expansion_array__returns_interpolated_expansion(self):
        scopes = ["some:{scope}", "another:scope"]

        self.assertListEqual(
            sorted(expand_scopes(scopes, {"scope": ["epic"]})), ["another:scope", "some:epic"]
        )

    def test__multiple_expansion_arrays__returns_interpolated_expansion(self):
        scopes = ["some:{scope}", "another:scope"]

        self.assertListEqual(
            sorted(expand_scopes(scopes, {"scope": ["epic", "epic2"]})),
            sorted(["another:scope", "some:epic", "some:epic2"]),
        )


class TestExpandScopesFromContext(TestCase):
    def test__expand_with_various_objects__succeeds(self):
        scopes = [
            "some:{scope}",
            "some:{deep.context.variable}",
            "some:{class.property}",
        ]

        class SomeClass:
            def __init__(self):
                self.property = "Hi there"

        self.assertListEqual(
            sorted(
                expand_scopes_from_context(
                    scopes,
                    {
                        "scope": 2,
                        "deep": {"context": {"variable": 5}},
                        "class": SomeClass(),
                    },
                )
            ),
            sorted(["some:2", "some:5", "some:Hi there"]),
        )

    def test__expand_with_arrays__calculates_the_products(self):
        scopes = [
            "some:{scope}",
            "some:{deep.context.variable}",
            "some:{class.property}",
        ]

        class SomeClass:
            def __init__(self):
                self.property = "Hi there"

        self.assertListEqual(
            sorted(
                expand_scopes_from_context(
                    scopes,
                    {
                        "scope": [2, 3],
                        "deep": {"context": {"variable": ["result-1", "result-2"]}},
                        "class": SomeClass(),
                    },
                )
            ),
            sorted(
                ["some:2", "some:3", "some:result-1", "some:result-2", "some:Hi there"]
            ),
        )
