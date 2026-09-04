"""Synthetic image tests for generic minimap progress extraction."""

import unittest
from unittest.mock import patch

import cv2
import numpy as np

from acc_telemetry.extraction.map_progress import (
    CenterlineTopologyError,
    build_centerline,
    extract_red_candidates,
    project_candidate,
)
from acc_telemetry.domain.progress import Centerline, RedDotCandidate


def _build(mask: np.ndarray):
    return build_centerline(
        mask.astype(np.float32) / 255.0,
        frequency_threshold=0.45,
        max_branch_length_fraction=0.03,
        min_cycle_diagonal_fraction=2.0,
        resample_spacing_diagonal_fraction=0.01,
    )


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


class TestCenterline(unittest.TestCase):
    def test_orders_and_resamples_one_thick_closed_ring(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.rectangle(mask, (20, 20), (180, 180), 255, 9)

        centerline = _build(mask)

        self.assertGreater(len(centerline.points), 100)
        self.assertEqual(centerline.cumulative_length_px[0], 0.0)
        self.assertTrue(
            all(
                current > previous
                for previous, current in zip(
                    centerline.cumulative_length_px,
                    centerline.cumulative_length_px[1:],
                )
            )
        )
        self.assertGreater(
            centerline.total_length_px,
            centerline.cumulative_length_px[-1],
        )
        segment_lengths = [
            np.linalg.norm(np.subtract(second, first))
            for first, second in zip(centerline.points, centerline.points[1:])
        ]
        expected_spacing = np.hypot(*mask.shape) * 0.01
        self.assertLess(max(abs(length - expected_spacing) for length in segment_lengths), 1.1)

    def test_prunes_a_short_start_marker_branch(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.rectangle(mask, (20, 20), (180, 180), 255, 9)
        cv2.line(mask, (100, 20), (100, 10), 255, 5)

        centerline = _build(mask)

        self.assertGreater(len(centerline.points), 100)
        self.assertTrue(all(y >= 18.0 for _, y in centerline.points))

    def test_prunes_neighbouring_short_branches_in_one_topology_pass(self):
        mask = np.zeros((240, 240), dtype=np.uint8)
        cv2.rectangle(mask, (20, 20), (220, 220), 255, 9)
        cv2.line(mask, (100, 20), (94, 10), 255, 3)
        cv2.line(mask, (100, 20), (106, 10), 255, 3)

        centerline = _build(mask)

        self.assertGreater(len(centerline.points), 100)
        self.assertTrue(all(y >= 18.0 for _, y in centerline.points))

    def test_removes_short_transverse_markers_from_the_closed_cycle(self):
        mask = np.zeros((240, 240), dtype=np.uint8)
        cv2.rectangle(mask, (20, 20), (220, 220), 255, 1)
        cv2.line(mask, (98, 20), (100, 16), 255, 1)
        cv2.line(mask, (100, 16), (102, 20), 255, 1)

        centerline = _build(mask)

        self.assertGreater(len(centerline.points), 100)
        self.assertTrue(
            all(18.0 <= x <= 222.0 and 18.0 <= y <= 222.0 for x, y in centerline.points)
        )

    def test_adjacent_pixels_on_opposite_stroke_edges_remain_local(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.rectangle(mask, (20, 20), (180, 180), 255, 11)
        centerline = _build(mask)

        def nearest_progress(point):
            distances = [
                np.linalg.norm(np.subtract(candidate, point))
                for candidate in centerline.points
            ]
            index = int(np.argmin(distances))
            return centerline.cumulative_length_px[index] / centerline.total_length_px

        outer_progress = nearest_progress((100.0, 15.0))
        inner_progress = nearest_progress((100.0, 25.0))
        wrapped_difference = abs(((outer_progress - inner_progress + 0.5) % 1.0) - 0.5)

        self.assertLess(wrapped_difference, 0.02)

    def test_rejects_an_open_path_without_fallback(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.line(mask, (20, 100), (180, 100), 255, 9)

        with self.assertRaises(CenterlineTopologyError) as caught:
            _build(mask)

        self.assertEqual(caught.exception.reason, "no_closed_cycle")

    def test_rejects_multiple_unresolved_cycles(self):
        mask = np.zeros((240, 240), dtype=np.uint8)
        cv2.circle(mask, (60, 120), 40, 255, 9)
        cv2.circle(mask, (180, 120), 40, 255, 9)

        with self.assertRaises(CenterlineTopologyError) as caught:
            _build(mask)

        self.assertEqual(caught.exception.reason, "multiple_cycles")

    def test_keeps_a_dominant_cycle_over_small_disconnected_loop_artifacts(self):
        mask = np.zeros((240, 240), dtype=np.uint8)
        cv2.rectangle(mask, (20, 20), (220, 220), 255, 9)
        cv2.circle(mask, (110, 110), 10, 255, 3)

        centerline = _build(mask)

        self.assertGreater(len(centerline.points), 100)
        self.assertTrue(all(x <= 225.0 and y <= 225.0 for x, y in centerline.points))

    def test_selects_the_only_long_closed_component_when_a_distractor_is_larger(self):
        mask = np.zeros((500, 500), dtype=np.uint8)
        cv2.rectangle(mask, (10, 10), (490, 490), 255, 5)
        cv2.rectangle(mask, (140, 170), (360, 330), 255, -1)
        cv2.circle(mask, (205, 250), 35, 0, -1)
        cv2.circle(mask, (295, 250), 35, 0, -1)

        centerline = _build(mask)

        xs = [point[0] for point in centerline.points]
        ys = [point[1] for point in centerline.points]
        self.assertLess(min(xs), 20.0)
        self.assertGreater(max(xs), 480.0)
        self.assertLess(min(ys), 20.0)
        self.assertGreater(max(ys), 480.0)

    def test_rejects_an_excessive_branch(self):
        mask = np.zeros((240, 240), dtype=np.uint8)
        cv2.rectangle(mask, (30, 30), (210, 210), 255, 9)
        cv2.line(mask, (120, 30), (120, 110), 255, 7)

        with self.assertRaises(CenterlineTopologyError) as caught:
            _build(mask)

        self.assertEqual(caught.exception.reason, "excessive_branches")

    def test_rejects_disconnected_noncycle_components(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.line(mask, (20, 50), (180, 50), 255, 9)
        cv2.line(mask, (20, 150), (180, 150), 255, 9)

        with self.assertRaises(CenterlineTopologyError) as caught:
            _build(mask)

        self.assertEqual(caught.exception.reason, "discontinuous_path")

    def test_rejects_an_implausibly_short_cycle(self):
        mask = np.zeros((200, 200), dtype=np.uint8)
        cv2.circle(mask, (100, 100), 20, 255, 7)

        with self.assertRaises(CenterlineTopologyError) as caught:
            _build(mask)

        self.assertEqual(caught.exception.reason, "implausibly_short_path")


class TestProjection(unittest.TestCase):
    def setUp(self):
        self.square = Centerline(
            points=((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0)),
            cumulative_length_px=(0.0, 10.0, 20.0, 30.0),
            total_length_px=40.0,
        )

    @staticmethod
    def candidate(x: float, y: float) -> RedDotCandidate:
        return RedDotCandidate((x, y), 50.0, 0.001, 0.9)

    def test_projects_orthogonally_onto_a_centerline_segment(self):
        projections = project_candidate(
            self.candidate(5.0, 2.0),
            self.square,
            max_distance_px=3.0,
        )

        self.assertEqual(len(projections), 1)
        self.assertAlmostEqual(projections[0].s_visual, 0.125)
        self.assertAlmostEqual(projections[0].distance_px, 2.0)
        self.assertEqual(projections[0].projected_xy, (5.0, 0.0))

    def test_preserves_progress_wraparound_on_the_closing_segment(self):
        near_end = project_candidate(
            self.candidate(1.0, 1.0),
            self.square,
            max_distance_px=1.1,
        )

        self.assertEqual(
            sorted(round(projection.s_visual, 3) for projection in near_end),
            [0.025, 0.975],
        )

    def test_returns_multiple_nearby_branch_projections_without_choosing(self):
        parallel = Centerline(
            points=((0.0, 0.0), (10.0, 0.0), (10.0, 2.0), (0.0, 2.0)),
            cumulative_length_px=(0.0, 10.0, 12.0, 22.0),
            total_length_px=24.0,
        )

        projections = project_candidate(
            self.candidate(5.0, 1.0),
            parallel,
            max_distance_px=1.1,
        )

        self.assertGreaterEqual(len(projections), 2)
        self.assertIn(0.208, [round(projection.s_visual, 3) for projection in projections])
        self.assertIn(0.708, [round(projection.s_visual, 3) for projection in projections])

    def test_collapses_adjacent_segments_into_one_local_projection(self):
        dense = Centerline(
            points=tuple((float(x), 0.0) for x in range(11))
            + ((10.0, 10.0), (0.0, 10.0)),
            cumulative_length_px=tuple(float(x) for x in range(11)) + (20.0, 30.0),
            total_length_px=40.0,
        )

        projections = project_candidate(
            self.candidate(5.0, 0.5),
            dense,
            max_distance_px=2.0,
        )

        self.assertEqual(len(projections), 1)
        self.assertAlmostEqual(projections[0].s_visual, 0.125)

    def test_rejects_segments_outside_the_geometric_gate(self):
        projections = project_candidate(
            self.candidate(50.0, 50.0),
            self.square,
            max_distance_px=3.0,
        )

        self.assertEqual(projections, ())


if __name__ == "__main__":
    unittest.main()
