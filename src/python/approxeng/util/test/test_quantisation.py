from unittest import TestCase

from approxeng.util import quantise_to


class TestQuantisation(TestCase):

    def test_quantisation(self):
        q = quantise_to(source_low=0, source_high=1, max_level=10)
        self.assertEqual(q(0.51), 5)
        self.assertEqual(q(0.08), 0)
        self.assertEqual(q(0.10), 1)

    def test_quantisation_with_pad(self):
        q = quantise_to(source_low=0, source_high=1, max_level=10, low_pad=0.5, high_pad=0.5)
        self.assertEqual(q(0), 0)
        self.assertEqual(q(0.05), 1)
        self.assertEqual(q(0.95), 10)
