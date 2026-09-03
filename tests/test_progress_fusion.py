"""Tests for odometry-guided visual selection and fused progress."""

import unittest

from acc_telemetry.application.odometry import OdometryPoint
from acc_telemetry.application.progress import (
    FusedProgressEstimator,
    ProgressReplayObservation,
    VisualSelection,
    estimate_progress,
    select_visual_projection,
)
from acc_telemetry.extraction.map_progress import VisualProjection
from acc_telemetry.domain.progress import ConfirmedLapBoundary, ProgressSource


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


def _odometry(
    time_s: float,
    distance_m: float,
    delta_distance_m: float | None,
    *,
    source: ProgressSource = ProgressSource.OBSERVED,
    uncertainty: float = 0.001,
) -> OdometryPoint:
    return OdometryPoint(
        time_s,
        distance_m,
        delta_distance_m,
        uncertainty,
        source,
        (),
    )


def _visual(s_visual: float | None, *, uncertainty: float = 0.001) -> VisualSelection:
    if s_visual is None:
        return VisualSelection(
            None,
            None,
            None,
            uncertainty,
            ProgressSource.MISSING,
            ("visual_missing",),
        )
    return VisualSelection(
        s_visual,
        (10.0, 10.0),
        0.0,
        uncertainty,
        ProgressSource.OBSERVED,
        ("visual_selected",),
    )


def _boundary(time_s: float, from_lap: int = 8) -> ConfirmedLapBoundary:
    return ConfirmedLapBoundary(
        frame=int(time_s * 60),
        time_s=time_s,
        from_lap=from_lap,
        to_lap=from_lap + 1,
        confidence=1.0,
    )


class TestFusedEstimator(unittest.TestCase):
    def setUp(self):
        self.estimator = FusedProgressEstimator(
            effective_lap_length_m=1000.0,
            visual_gain=0.35,
            short_visual_gap_s=0.5,
            unavailable_uncertainty=0.05,
        )

    def test_remains_unanchored_before_first_confirmed_boundary(self):
        estimate = self.estimator.update(
            _odometry(0.0, 0.0, None),
            _visual(0.25),
            boundary=None,
        )

        self.assertIsNone(estimate.s_fused)
        self.assertIsNone(estimate.s_odometry)
        self.assertFalse(estimate.anchored)
        self.assertEqual(estimate.reasons, ("unanchored",))

    def test_confirmed_boundary_is_the_only_zero_anchor(self):
        estimate = self.estimator.update(
            _odometry(1.0, 100.0, 10.0),
            _visual(None),
            boundary=_boundary(1.0),
        )

        self.assertEqual(estimate.s_fused, 0.0)
        self.assertEqual(estimate.s_odometry, 0.0)
        self.assertTrue(estimate.anchored)
        self.assertIn("lap_boundary_confirmed", estimate.reasons)

    def test_fuses_visual_correction_into_odometric_prediction(self):
        self.estimator.update(_odometry(0.0, 0.0, None), _visual(None), _boundary(0.0))

        estimate = self.estimator.update(
            _odometry(0.1, 100.0, 100.0),
            _visual(0.11),
            boundary=None,
        )

        self.assertAlmostEqual(estimate.s_odometry, 0.1)
        self.assertAlmostEqual(estimate.s_visual, 0.11)
        self.assertAlmostEqual(estimate.s_fused, 0.1035)
        self.assertEqual(estimate.source, ProgressSource.FUSED)

    def test_short_visual_gap_is_explicitly_predicted(self):
        self.estimator.update(_odometry(0.0, 0.0, None), _visual(None), _boundary(0.0))
        observed = self.estimator.update(
            _odometry(0.1, 100.0, 100.0), _visual(0.1), None
        )

        predicted = self.estimator.update(
            _odometry(0.3, 120.0, 20.0), _visual(None), None
        )

        self.assertEqual(predicted.source, ProgressSource.PREDICTED)
        self.assertGreater(predicted.uncertainty, observed.uncertainty)
        self.assertIsNotNone(predicted.s_fused)

    def test_interpolated_odometry_remains_explicit(self):
        self.estimator.update(_odometry(0.0, 0.0, None), _visual(None), _boundary(0.0))

        estimate = self.estimator.update(
            _odometry(
                0.1,
                10.0,
                10.0,
                source=ProgressSource.INTERPOLATED,
                uncertainty=0.01,
            ),
            _visual(None),
            None,
        )

        self.assertEqual(estimate.source, ProgressSource.INTERPOLATED)
        self.assertIn("speed_gap_interpolated", estimate.reasons)

    def test_long_visual_gap_becomes_unavailable(self):
        self.estimator.update(_odometry(0.0, 0.0, None), _visual(None), _boundary(0.0))
        self.estimator.update(_odometry(0.1, 100.0, 100.0), _visual(0.1), None)

        estimate = self.estimator.update(
            _odometry(1.0, 190.0, 90.0), _visual(None), None
        )

        self.assertIsNone(estimate.s_fused)
        self.assertEqual(estimate.source, ProgressSource.MISSING)
        self.assertIn("uncertainty_limit", estimate.reasons)

    def test_visual_wrap_cannot_reset_without_a_boundary(self):
        self.estimator.update(_odometry(0.0, 0.0, None), _visual(None), _boundary(0.0))
        self.estimator.update(_odometry(1.0, 990.0, 990.0), _visual(0.99), None)

        estimate = self.estimator.update(
            _odometry(1.1, 1000.0, 10.0),
            _visual(0.005),
            None,
        )

        self.assertGreaterEqual(estimate.s_fused, 0.99)
        self.assertNotIn("lap_boundary_confirmed", estimate.reasons)


class TestOfflineProgressReplay(unittest.TestCase):
    def test_rebases_only_complete_boundary_to_boundary_laps(self):
        observations = [
            ProgressReplayObservation(_odometry(0.0, 0.0, None), _visual(None), None),
            ProgressReplayObservation(_odometry(10.0, 100.0, 100.0), _visual(None), _boundary(10.0, 7)),
            ProgressReplayObservation(_odometry(20.0, 1100.0, 1000.0), _visual(None), _boundary(20.0, 8)),
            ProgressReplayObservation(_odometry(30.0, 2100.0, 1000.0), _visual(None), _boundary(30.0, 9)),
        ]

        replay = estimate_progress(
            observations,
            max_missing_speed_fraction=0.01,
            max_relative_mad=0.03,
            visual_gain=0.35,
            short_visual_gap_s=0.5,
            unavailable_uncertainty=0.05,
        )

        self.assertEqual(replay.calibration.effective_lap_length_m, 1000.0)
        self.assertIsNone(replay.estimates[0].s_fused)
        self.assertFalse(replay.estimates[0].anchored)
        self.assertEqual(replay.estimates[1].s_fused, 0.0)
        self.assertEqual(replay.estimates[2].s_fused, 0.0)

    def test_crash_distance_outlier_does_not_recalibrate(self):
        boundaries = [_boundary(0.0, 7), _boundary(10.0, 8), _boundary(20.0, 9), _boundary(30.0, 10)]
        distances = [0.0, 1000.0, 2000.0, 5000.0]
        observations = [
            ProgressReplayObservation(
                _odometry(boundary.time_s, distance, None),
                _visual(None),
                boundary,
            )
            for boundary, distance in zip(boundaries, distances)
        ]

        replay = estimate_progress(
            observations,
            max_missing_speed_fraction=0.01,
            max_relative_mad=0.03,
            visual_gain=0.35,
            short_visual_gap_s=0.5,
            unavailable_uncertainty=0.05,
        )

        self.assertEqual(replay.calibration.effective_lap_length_m, 1000.0)
        self.assertEqual(
            [lap.lap_number for lap in replay.calibration.rejected_laps],
            [10],
        )


if __name__ == "__main__":
    unittest.main()
