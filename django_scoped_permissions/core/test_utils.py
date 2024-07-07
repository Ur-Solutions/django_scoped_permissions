from django.test import TestCase

from django_scoped_permissions.core.utils import interpolate_context


class TestInterpolateContext(TestCase):
    def test_interpolate_context(self):
        self.assertEqual("Hi there", interpolate_context("Hi there", {}))

    def test_interpolate_context_with_variables(self):
        self.assertEqual("Hi there", interpolate_context("Hi {var}", {"var": "there"}))

    def test_interpolate_with_nested_variables(self):
        self.assertEqual("Hi there", interpolate_context("Hi {var.var2}", {"var": {"var2": "there"}}))

    def test_interpolate_context_with_variables_and_context(self):
        self.assertEqual("Hi ", interpolate_context("Hi {var}", {"var2": "there"}, strict_mode=False))

    def test_interpolate_context_with_variables_and_context_strict_mode(self):
        with self.assertRaises(Exception):
            interpolate_context("Hi {var}", {"var2": "there"}, strict_mode=True)