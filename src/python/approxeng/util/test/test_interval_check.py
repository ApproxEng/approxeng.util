import time
from unittest import TestCase

from approxeng.util import IntervalCheck


class TestIntervalCheck(TestCase):
    """
    Tests for the IntervalCheck class
    """

    def test_init(self):
        i = IntervalCheck(interval=1)
        self.assertTrue(i.should_run())
        self.assertFalse(i.should_run())
        time.sleep(1)
        self.assertTrue(i.should_run())
