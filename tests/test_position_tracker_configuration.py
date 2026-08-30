"""Tests for position tracker profile configuration."""

import unittest

import numpy as np

from src.position_tracker_v2 import PositionTrackerV2


class TestPositionTrackerConfiguration(unittest.TestCase):
    def test_accepts_custom_white_bounds(self):
        tracker = PositionTrackerV2(
            white_lower=[0, 0, 150],
            white_upper=[180, 100, 255],
        )

        np.testing.assert_array_equal(tracker.white_lower, [0, 0, 150])
        np.testing.assert_array_equal(tracker.white_upper, [180, 100, 255])


if __name__ == "__main__":
    unittest.main()
