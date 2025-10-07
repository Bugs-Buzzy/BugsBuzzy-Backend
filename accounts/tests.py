import pytest
from django.test import TestCase


class SampleTest(TestCase):
    def test_example(self):
        assert 1 + 1 == 2
