"""Tests for odometry-guided visual selection and fused progress."""

import unittest

from acc_telemetry.application.progress import select_visual_projection
from acc_telemetry.extraction.map_progress import VisualProjection
from acc_telemetry.domain.progress import ProgressSource


def _projection(
    s_visual: float,
    *,
    distance_px: float = 1.0,
    centroid: tuple[float, float] = (10.0, 10.0),
) -> VisualProjection:
    return VisualProjection(
        s_visual=s_visual,
        distance_px=distance_px,
        projected_xy=centroid,
        centroid=centroid,
    )


def _select(projections, **overrides):
    arguments = {
        "predicted_s": 0.018,
        "current_uncertainty": 0.002,
        "last_centroid": (9.0, 10.0),
        "previous_displacement_px": 1.0,
        "speed_kmh": 100.0,
        "delta_time_s": 0.1,
        "roi_diagonal_px": 500.0,
        "max_centerline_distance_diagonal_fraction": 0.03,
        "max_progress_error": 0.04,
        "min_score_margin": 0.15,
    }
    arguments.update(overrides)
    return select_visual_projection(projections, **arguments)


class TestVisualSelection(unittest.TestCase):
    def test_selects_the_branch_compatible_with_odometric_prediction(self):
        selection = _select(
            (
                _projection(0.015, distance_px=2.0, centroid=(10.0, 10.0)),
                _projection(0.347, distance_px=1.0, centroid=(10.0, 11.0)),
            )
        )

        self.assertEqual(selection.s_visual, 0.015)
        self.assertEqual(selection.source, ProgressSource.OBSERVED)
        self.assertEqual(selection.reasons, ("visual_selected",))

    def test_uses_wrapped_progress_error_near_start_finish(self):
        selection = _select(
            (_projection(0.005),),
            predicted_s=0.995,
            last_centroid=None,
        )

        self.assertEqual(selection.s_visual, 0.005)

    def test_rejects_a_tie_as_ambiguous(self):
        selection = _select(
            (
                _projection(0.020, centroid=(10.0, 10.0)),
                _projection(0.020, centroid=(10.0, 10.0)),
            ),
            predicted_s=0.020,
        )

        self.assertIsNone(selection.s_visual)
        self.assertEqual(selection.source, ProgressSource.MISSING)
        self.assertEqual(selection.reasons, ("visual_ambiguous",))

    def test_image_continuity_can_break_a_geometric_tie(self):
        selection = _select(
            (
                _projection(0.020, centroid=(100.0, 100.0)),
                _projection(0.025, centroid=(10.0, 10.0)),
            ),
            predicted_s=0.020,
        )

        self.assertEqual(selection.s_visual, 0.025)

    def test_rejects_every_projection_outside_the_progress_gate(self):
        selection = _select((_projection(0.2),))

        self.assertIsNone(selection.s_visual)
        self.assertEqual(selection.reasons, ("visual_out_of_gate",))

    def test_odometric_uncertainty_expands_the_progress_gate(self):
        selection = _select(
            (_projection(0.065),),
            predicted_s=0.02,
            current_uncertainty=0.01,
            last_centroid=None,
        )

        self.assertEqual(selection.s_visual, 0.065)

    def test_stationary_speed_rejects_nonlocal_image_motion(self):
        selection = _select(
            (_projection(0.02, centroid=(100.0, 100.0)),),
            predicted_s=0.02,
            speed_kmh=0.0,
        )

        self.assertIsNone(selection.s_visual)
        self.assertEqual(selection.reasons, ("visual_out_of_gate",))

    def test_reports_missing_when_no_candidate_was_projected(self):
        selection = _select(())

        self.assertIsNone(selection.s_visual)
        self.assertEqual(selection.source, ProgressSource.MISSING)
        self.assertEqual(selection.reasons, ("visual_missing",))


if __name__ == "__main__":
    unittest.main()
