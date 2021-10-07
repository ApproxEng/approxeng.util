import random
from unittest import TestCase

from approxeng.util import interpolator


def random_pair(min_distance=0.0001):
    """
    We get errors to do with insufficient precision in the interpolation tests if the high and low ends
    of the range are too similar, so use this function to generate a pair of random numbers with a guaranteed
    minimum delta

    :return: a pair of random numbers 0<=[a,b]<=1.0 such that abs(a-b) >= min_distance
    """
    while True:
        a, b = random.random(), random.random()
        if abs(a - b) > min_distance:
            return a, b


class TestInterpolation(TestCase):
    """
    Tests for interpolation logic
    """

    def test_interpolator_identity_function(self):
        """
        Creates random unlocked interpolator functions with the same low and high values for
        source and dest and checks them against a range of inputs
        """
        for low, high in [random_pair() for _ in range(100)]:
            i = interpolator(low, high, low, high, False)
            for value in range(-100, 100):
                self.assertAlmostEqual(i(value), value, places=10,
                                       msg=f'low={low}, high={high}, value={value}')

    def test_illegal_constructor(self):
        """
        Should fail to build an interpolator with equal low and high source values
        """
        with self.assertRaises(ValueError):
            i = interpolator(source_low=1, source_high=1)

    def test_interpolator_inverse_function(self):
        """
        As above, but checks that the function returns the negated form by swapping the input
        and output high / low values
        """
        i = interpolator(source_low=1, source_high=2, dest_low=2, dest_high=1, lock_range=False)
        self.assertEqual(i(0), 3)
        for low, high in [random_pair() for _ in range(100)]:
            i = interpolator(low, high, high, low, False)
            for value in range(-100, 100):
                self.assertAlmostEqual(i(float(value)), (low + high) - value, places=10,
                                       msg=f'low={low}, high={high}, value={value}')
