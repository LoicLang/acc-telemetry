"""Synthetic image tests for generic minimap progress extraction."""

import unittest
from unittest.mock import patch

import cv2
import numpy as np

from acc_telemetry.extraction.map_progress import extract_red_candidates


class TestRedDotCandidates(unittest.TestCase):
    def test_keeps_all_plausible_dots_despite_a_larger_red_region(self):
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        image[0:31, 0:31] = (0, 0, 255)
        cv2.circle(image, (70, 30), 5, (0, 0, 255), -1)
        cv2.circle(image, (72, 70), 5, (0, 0, 255), -1)

        candidates = extract_red_candidates(
            image,
            min_area_fraction=0.00002,
            max_area_fraction=0.005,
            min_circularity=0.35,
        )

        self.assertEqual(
            [candidate.centroid for candidate in candidates],
            [(70.0, 30.0), (72.0, 70.0)],
        )
        self.assertTrue(
            all(candidate.area_fraction < 0.005 for candidate in candidates)
        )

    def test_returns_empty_for_missing_or_empty_images(self):
        settings = {
            "min_area_fraction": 0.00002,
            "max_area_fraction": 0.005,
            "min_circularity": 0.35,
        }

        self.assertEqual(extract_red_candidates(None, **settings), ())
        self.assertEqual(
            extract_red_candidates(np.zeros((0, 0, 3), dtype=np.uint8), **settings),
            (),
        )

    def test_rejects_tiny_and_elongated_red_regions_individually(self):
        image = np.zeros((200, 200, 3), dtype=np.uint8)
        image[10, 10] = (0, 0, 255)
        image[80:83, 50:100] = (0, 0, 255)
        cv2.circle(image, (150, 150), 5, (0, 0, 255), -1)

        candidates = extract_red_candidates(
            image,
            min_area_fraction=0.0005,
            max_area_fraction=0.005,
            min_circularity=0.6,
        )

        self.assertEqual(
            [candidate.centroid for candidate in candidates],
            [(150.0, 150.0)],
        )

    def test_detects_candidates_in_both_red_hue_ranges(self):
        hsv = np.zeros((200, 200, 3), dtype=np.uint8)
        cv2.circle(hsv, (40, 40), 5, (5, 255, 255), -1)
        cv2.circle(hsv, (160, 160), 5, (175, 255, 255), -1)
        image = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

        candidates = extract_red_candidates(
            image,
            min_area_fraction=0.0005,
            max_area_fraction=0.005,
            min_circularity=0.35,
        )

        self.assertEqual(
            [candidate.centroid for candidate in candidates],
            [(40.0, 40.0), (160.0, 160.0)],
        )

    def test_skips_a_contour_with_zero_moment(self):
        image = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.circle(image, (50, 50), 5, (0, 0, 255), -1)

        with patch(
            "acc_telemetry.extraction.map_progress.cv2.moments",
            return_value={"m00": 0.0, "m10": 0.0, "m01": 0.0},
        ):
            candidates = extract_red_candidates(
                image,
                min_area_fraction=0.0005,
                max_area_fraction=0.02,
                min_circularity=0.35,
            )

        self.assertEqual(candidates, ())


if __name__ == "__main__":
    unittest.main()
