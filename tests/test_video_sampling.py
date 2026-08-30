"""Tests for video frame sampling helpers."""

import unittest

from src.video_processor import evenly_spaced_frame_indices


class TestEvenlySpacedFrameIndices(unittest.TestCase):
    def test_samples_full_video_range(self):
        self.assertEqual(
            evenly_spaced_frame_indices(100, 5),
            [0, 24, 49, 74, 99],
        )

    def test_limits_samples_to_available_frames(self):
        self.assertEqual(evenly_spaced_frame_indices(3, 60), [0, 1, 2])

    def test_returns_empty_list_for_empty_video(self):
        self.assertEqual(evenly_spaced_frame_indices(0, 60), [])


if __name__ == "__main__":
    unittest.main()
