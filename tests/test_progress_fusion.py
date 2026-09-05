"""Tests for odometry-guided visual selection and fused progress."""

import unittest

import cv2
import numpy as np

from acc_telemetry.application.odometry import OdometryPoint
from acc_telemetry.application.progress import (
    AnchorFrameEvidence,
    BoundaryAnchorSource,
    BoundaryVisualAnchor,
    FusedProgressEstimator,
    ProgressReplayObservation,
    ProgressSessionEstimator,
    VisualSelection,
    estimate_progress,
    infer_centerline_direction,
    recover_boundary_visual_anchor,
    select_visual_projection,
)
from acc_telemetry.extraction.map_progress import VisualProjection
from acc_telemetry.domain.progress import Centerline, ConfirmedLapBoundary, ProgressSource
from acc_telemetry.application.config import BoundaryAnchorSettings, load_settings
from acc_telemetry.application.lap_state import LapTransitionConfirmer


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


class TestCenterlineDirection(unittest.TestCase):
    def test_does_not_lock_direction_from_submargin_jitter(self):
        direction = infer_centerline_direction(
            (_projection(0.00001),),
            anchor_s=0.0,
            predicted_s=0.0001,
            min_error_margin=0.006,
        )

        self.assertIsNone(direction)

    def test_selects_reverse_order_when_it_matches_odometry(self):
        direction = infer_centerline_direction(
            (_projection(0.99),),
            anchor_s=0.0,
            predicted_s=0.01,
            min_error_margin=0.006,
        )

        self.assertEqual(direction, -1)

    def test_selects_forward_order_when_it_matches_odometry(self):
        direction = infer_centerline_direction(
            (_projection(0.01),),
            anchor_s=0.0,
            predicted_s=0.01,
            min_error_margin=0.006,
        )

        self.assertEqual(direction, 1)


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


def _exact_anchor(raw_s: float = 0.0) -> BoundaryVisualAnchor:
    return BoundaryVisualAnchor(
        raw_s=raw_s,
        centroid=(10.0, 10.0),
        uncertainty=0.0,
        source=BoundaryAnchorSource.EXACT,
    )


def _anchor_settings() -> BoundaryAnchorSettings:
    return BoundaryAnchorSettings(
        max_bracketing_gap_s=0.25,
        max_bracketing_distance_fraction=0.005,
        max_one_sided_gap_s=0.10,
        max_one_sided_distance_fraction=0.002,
    )


def _anchor_frame(
    time_s: float,
    distance_m: float,
    projections: tuple[VisualProjection, ...] = (),
    boundary: ConfirmedLapBoundary | None = None,
) -> AnchorFrameEvidence:
    return AnchorFrameEvidence(time_s, distance_m, projections, boundary)


class TestBoundaryVisualAnchor(unittest.TestCase):
    def _recover(
        self,
        frames,
        *,
        boundary_index,
        last_raw_s=None,
        effective_lap_length_m=1000.0,
        min_score_margin=0.15,
    ):
        return recover_boundary_visual_anchor(
            tuple(frames),
            boundary_index=boundary_index,
            effective_lap_length_m=effective_lap_length_m,
            last_raw_s=last_raw_s,
            max_centerline_distance_px=10.0,
            max_progress_error=0.04,
            min_score_margin=min_score_margin,
            unavailable_uncertainty=0.05,
            settings=_anchor_settings(),
        )

    def test_exact_projection_is_preferred_without_added_uncertainty(self):
        frames = (
            _anchor_frame(0.9, 99.0, (_projection(0.998),)),
            _anchor_frame(1.0, 100.0, (_projection(0.002),), _boundary(1.0)),
            _anchor_frame(1.1, 101.0, (_projection(0.006),)),
        )

        anchor = self._recover(frames, boundary_index=1, last_raw_s=0.999)

        self.assertIsInstance(anchor, BoundaryVisualAnchor)
        self.assertEqual(anchor.source, BoundaryAnchorSource.EXACT)
        self.assertEqual(anchor.raw_s, 0.002)
        self.assertEqual(anchor.centroid, (10.0, 10.0))
        self.assertEqual(anchor.uncertainty, 0.0)

    def test_refuses_to_recover_without_a_confirmed_boundary(self):
        frames = (_anchor_frame(1.0, 100.0, (_projection(0.002),)),)

        anchor = self._recover(frames, boundary_index=0)

        self.assertEqual(anchor.source, BoundaryAnchorSource.MISSING)

    def test_rejects_equal_exact_scores_when_margin_is_zero(self):
        frames = (
            _anchor_frame(
                1.0,
                100.0,
                (
                    _projection(0.001, centroid=(9.0, 10.0)),
                    _projection(0.002, centroid=(11.0, 10.0)),
                ),
                _boundary(1.0),
            ),
        )

        anchor = self._recover(frames, boundary_index=0, min_score_margin=0.0)

        self.assertEqual(anchor.source, BoundaryAnchorSource.MISSING)

    def test_interpolates_across_the_wrapped_start_finish_interval(self):
        frames = (
            _anchor_frame(0.9, 99.0, (_projection(0.998),)),
            _anchor_frame(1.0, 100.0, boundary=_boundary(1.0)),
            _anchor_frame(1.1, 101.0, (_projection(0.002),)),
        )

        anchor = self._recover(
            frames,
            boundary_index=1,
            effective_lap_length_m=2000.0,
        )

        self.assertEqual(anchor.source, BoundaryAnchorSource.INTERPOLATED)
        self.assertAlmostEqual(anchor.raw_s, 0.0)

    def test_weights_interpolation_by_odometry_instead_of_time(self):
        frames = (
            _anchor_frame(0.8, 100.0, (_projection(0.10),)),
            _anchor_frame(0.9, 102.0, boundary=_boundary(0.9)),
            _anchor_frame(1.0, 108.0, (_projection(0.14),)),
        )

        anchor = self._recover(
            frames,
            boundary_index=1,
            effective_lap_length_m=2000.0,
        )

        self.assertEqual(anchor.source, BoundaryAnchorSource.INTERPOLATED)
        self.assertAlmostEqual(anchor.raw_s, 0.11)

    def test_recovers_one_sided_projection_inside_both_strict_gates(self):
        frames = (
            _anchor_frame(0.92, 98.5, (_projection(0.997),)),
            _anchor_frame(1.0, 100.0, boundary=_boundary(1.0)),
        )

        anchor = self._recover(frames, boundary_index=1)

        self.assertEqual(anchor.source, BoundaryAnchorSource.NEAREST)
        self.assertEqual(anchor.raw_s, 0.997)
        self.assertGreater(anchor.uncertainty, 0.0)
        self.assertLessEqual(anchor.uncertainty, 0.025)

    def test_rejects_one_sided_projection_when_either_gate_fails(self):
        cases = (
            _anchor_frame(0.89, 99.0, (_projection(0.997),)),
            _anchor_frame(0.95, 97.9, (_projection(0.997),)),
        )

        for evidence in cases:
            with self.subTest(evidence=evidence):
                anchor = self._recover(
                    (evidence, _anchor_frame(1.0, 100.0, boundary=_boundary(1.0))),
                    boundary_index=1,
                )

                self.assertEqual(anchor.source, BoundaryAnchorSource.MISSING)
                self.assertIsNone(anchor.raw_s)
                self.assertIsNone(anchor.centroid)
                self.assertEqual(anchor.uncertainty, 0.05)

    def test_search_stops_at_another_confirmed_boundary(self):
        frames = (
            _anchor_frame(0.90, 99.0, (_projection(0.997),)),
            _anchor_frame(0.95, 99.5, boundary=_boundary(0.95, 7)),
            _anchor_frame(1.00, 100.0, boundary=_boundary(1.0, 8)),
        )

        anchor = self._recover(frames, boundary_index=2)

        self.assertEqual(anchor.source, BoundaryAnchorSource.MISSING)

    def test_rejects_equally_plausible_bracketing_pairs(self):
        frames = (
            _anchor_frame(
                0.9,
                99.0,
                (
                    _projection(0.998, centroid=(9.0, 10.0)),
                    _projection(0.998, centroid=(11.0, 10.0)),
                ),
            ),
            _anchor_frame(1.0, 100.0, boundary=_boundary(1.0)),
            _anchor_frame(1.1, 101.0, (_projection(0.002),)),
        )

        anchor = self._recover(frames, boundary_index=1)

        self.assertEqual(anchor.source, BoundaryAnchorSource.MISSING)

    def test_rejects_equal_bracketing_pair_scores_when_margin_is_zero(self):
        frames = (
            _anchor_frame(
                0.9,
                99.0,
                (
                    _projection(0.998, centroid=(9.0, 10.0)),
                    _projection(0.998, centroid=(11.0, 10.0)),
                ),
            ),
            _anchor_frame(1.0, 100.0, boundary=_boundary(1.0)),
            _anchor_frame(1.1, 101.0, (_projection(0.002),)),
        )

        anchor = self._recover(frames, boundary_index=1, min_score_margin=0.0)

        self.assertEqual(anchor.source, BoundaryAnchorSource.MISSING)

    def test_rejects_a_unique_bracketing_pair_inconsistent_with_odometry(self):
        frames = (
            _anchor_frame(0.9, 99.0, (_projection(0.10),)),
            _anchor_frame(1.0, 100.0, boundary=_boundary(1.0)),
            _anchor_frame(1.1, 101.0, (_projection(0.40),)),
        )

        anchor = self._recover(frames, boundary_index=1)

        self.assertEqual(anchor.source, BoundaryAnchorSource.MISSING)

    def test_skips_nonviable_frames_and_exact_evidence_during_scan(self):
        frames = (
            _anchor_frame(0.98, 99.8, (_projection(0.997, distance_px=1.0),)),
            _anchor_frame(0.99, 99.9, (_projection(0.998, distance_px=11.0),)),
            _anchor_frame(
                1.0,
                100.0,
                (_projection(0.002, distance_px=11.0),),
                _boundary(1.0),
            ),
        )

        anchor = self._recover(frames, boundary_index=2)

        self.assertEqual(anchor.source, BoundaryAnchorSource.NEAREST)
        self.assertEqual(anchor.raw_s, 0.997)


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

    def test_boundary_anchor_provenance_sets_source_reason_and_uncertainty(self):
        cases = (
            (BoundaryAnchorSource.EXACT, ProgressSource.OBSERVED, 0.0),
            (BoundaryAnchorSource.INTERPOLATED, ProgressSource.INTERPOLATED, 0.01),
            (BoundaryAnchorSource.NEAREST, ProgressSource.PREDICTED, 0.02),
            (BoundaryAnchorSource.MISSING, ProgressSource.OBSERVED, 0.05),
        )

        for anchor_source, expected_source, uncertainty in cases:
            with self.subTest(anchor_source=anchor_source):
                estimator = FusedProgressEstimator(
                    effective_lap_length_m=1000.0,
                    visual_gain=0.35,
                    short_visual_gap_s=0.5,
                    unavailable_uncertainty=0.05,
                )
                anchor = BoundaryVisualAnchor(
                    raw_s=(None if anchor_source is BoundaryAnchorSource.MISSING else 0.25),
                    centroid=(
                        None
                        if anchor_source is BoundaryAnchorSource.MISSING
                        else (10.0, 10.0)
                    ),
                    uncertainty=uncertainty,
                    source=anchor_source,
                )

                estimate = estimator.update(
                    _odometry(1.0, 100.0, 10.0),
                    _visual(None),
                    boundary=_boundary(1.0),
                    boundary_anchor=anchor,
                )

                self.assertEqual(estimate.s_fused, 0.0)
                self.assertEqual(estimate.s_odometry, 0.0)
                self.assertEqual(estimate.source, expected_source)
                self.assertEqual(estimate.uncertainty, uncertainty)
                self.assertEqual(
                    estimate.reasons,
                    ("lap_boundary_confirmed", anchor_source.value),
                )

    def test_calibration_unavailable_preserves_boundary_anchor_reason(self):
        estimator = FusedProgressEstimator(
            effective_lap_length_m=None,
            visual_gain=0.35,
            short_visual_gap_s=0.5,
            unavailable_uncertainty=0.05,
        )
        anchor = BoundaryVisualAnchor(
            raw_s=0.25,
            centroid=(10.0, 10.0),
            uncertainty=0.01,
            source=BoundaryAnchorSource.INTERPOLATED,
        )

        estimate = estimator.update(
            _odometry(1.0, 100.0, 10.0),
            _visual(None),
            boundary=_boundary(1.0),
            boundary_anchor=anchor,
        )

        self.assertEqual(
            estimate.reasons,
            (
                "lap_boundary_confirmed",
                "boundary_anchor_interpolated",
                "calibration_unavailable",
            ),
        )
        self.assertEqual(estimate.uncertainty, 0.01)

    def test_boundary_resets_session_accumulated_odometry_uncertainty(self):
        boundary_estimate = self.estimator.update(
            _odometry(1000.0, 70000.0, 10.0, uncertainty=0.2),
            _visual(None),
            boundary=_boundary(1000.0),
            boundary_anchor=_exact_anchor(),
        )
        next_estimate = self.estimator.update(
            _odometry(1000.1, 70010.0, 10.0, uncertainty=0.2001),
            _visual(0.01, uncertainty=0.001),
            boundary=None,
        )

        self.assertEqual(boundary_estimate.uncertainty, 0.0)
        self.assertIsNotNone(next_estimate.s_fused)
        self.assertEqual(next_estimate.source, ProgressSource.FUSED)

    def test_fuses_visual_correction_into_odometric_prediction(self):
        self.estimator.update(
            _odometry(0.0, 0.0, None),
            _visual(None),
            _boundary(0.0),
            boundary_anchor=_exact_anchor(),
        )

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
        self.estimator.update(
            _odometry(0.0, 0.0, None),
            _visual(None),
            _boundary(0.0),
            boundary_anchor=_exact_anchor(),
        )
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
        self.estimator.update(
            _odometry(0.0, 0.0, None),
            _visual(None),
            _boundary(0.0),
            boundary_anchor=_exact_anchor(),
        )

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
        self.estimator.update(
            _odometry(0.0, 0.0, None),
            _visual(None),
            _boundary(0.0),
            boundary_anchor=_exact_anchor(),
        )
        self.estimator.update(_odometry(0.1, 100.0, 100.0), _visual(0.1), None)

        estimate = self.estimator.update(
            _odometry(1.0, 190.0, 90.0), _visual(None), None
        )

        self.assertIsNone(estimate.s_fused)
        self.assertEqual(estimate.source, ProgressSource.MISSING)
        self.assertIn("uncertainty_limit", estimate.reasons)

    def test_visual_wrap_cannot_reset_without_a_boundary(self):
        self.estimator.update(
            _odometry(0.0, 0.0, None),
            _visual(None),
            _boundary(0.0),
            boundary_anchor=_exact_anchor(),
        )
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


class TestProgressSessionEstimator(unittest.TestCase):
    @staticmethod
    def _square_centerline() -> Centerline:
        return Centerline(
            points=(
                (100.0, 100.0),
                (1100.0, 100.0),
                (1100.0, 1100.0),
                (100.0, 1100.0),
            ),
            cumulative_length_px=(0.0, 1000.0, 2000.0, 3000.0),
            total_length_px=4000.0,
        )

    @staticmethod
    def _map_roi(position: tuple[int, int] | None) -> np.ndarray:
        roi = np.zeros((1200, 1200, 3), dtype=np.uint8)
        if position is not None:
            cv2.circle(roi, position, 10, (0, 0, 255), -1)
        return roi

    def test_recovers_first_boundary_anchor_and_fuses_the_following_lap(self):
        settings = load_settings().progress
        estimator = ProgressSessionEstimator(
            settings=settings,
            lap_confirmer=LapTransitionConfirmer(consecutive_observations=2),
            white_lower=(0, 0, 150),
            white_upper=(180, 100, 255),
            centerline=self._square_centerline(),
        )
        observations = (
            (0.00, 8, (480, 100)),
            (0.10, 8, (490, 100)),
            (9.95, 9, (490, 100)),
            (10.00, 9, None),
            (10.05, 9, (510, 100)),
            (10.50, 9, (600, 100)),
            (29.95, 10, (490, 100)),
            (30.00, 10, (500, 100)),
        )
        for frame, (time_s, lap_number, position) in enumerate(observations):
            estimator.observe_frame(
                frame=frame,
                time_s=time_s,
                speed_kmh=36.0,
                raw_lap_number=lap_number,
                map_roi=self._map_roi(position),
            )

        result = estimator.finalize()
        first_boundary_index = 3

        self.assertEqual(
            result.frames[first_boundary_index].boundary_anchor_source,
            BoundaryAnchorSource.INTERPOLATED,
        )
        self.assertEqual(result.frames[first_boundary_index].estimate.s_fused, 0.0)
        self.assertIsNotNone(
            result.frames[first_boundary_index + 2].estimate.s_visual
        )
        self.assertEqual(
            result.frames[first_boundary_index + 2].estimate.source,
            ProgressSource.FUSED,
        )
        self.assertEqual(
            sum(frame.boundary is not None for frame in result.frames),
            2,
        )

    def test_visual_wrap_without_confirmed_boundary_cannot_create_an_anchor_or_reset(self):
        settings = load_settings().progress
        estimator = ProgressSessionEstimator(
            settings=settings,
            lap_confirmer=LapTransitionConfirmer(consecutive_observations=2),
            white_lower=(0, 0, 150),
            white_upper=(180, 100, 255),
            centerline=self._square_centerline(),
        )
        for frame, position in enumerate(((110, 100), (100, 110), (110, 100))):
            estimator.observe_frame(
                frame=frame,
                time_s=frame * 0.1,
                speed_kmh=36.0,
                raw_lap_number=8,
                map_roi=self._map_roi(position),
            )

        result = estimator.finalize()

        self.assertTrue(
            all(frame.boundary_anchor_source is None for frame in result.frames)
        )
        self.assertTrue(all(frame.boundary is None for frame in result.frames))
        self.assertTrue(all(frame.estimate.s_fused is None for frame in result.frames))
        self.assertTrue(
            all("lap_boundary_confirmed" not in frame.estimate.reasons for frame in result.frames)
        )

    def test_prepares_a_centerline_from_stable_map_frames(self):
        settings = load_settings().progress
        estimator = ProgressSessionEstimator(
            settings=settings,
            lap_confirmer=LapTransitionConfirmer(consecutive_observations=2),
            white_lower=(0, 0, 150),
            white_upper=(180, 100, 255),
        )
        map_roi = np.zeros((200, 200, 3), dtype=np.uint8)
        cv2.rectangle(map_roi, (20, 20), (180, 180), (255, 255, 255), 9)

        prepared = estimator.prepare_map(
            [map_roi] * 10,
            frequency_threshold=0.45,
        )

        self.assertTrue(prepared)
        self.assertIsNotNone(estimator.centerline)
        self.assertIsNone(estimator.map_error_reason)

    def test_infers_centerline_direction_then_emits_anchored_visual_progress(self):
        settings = load_settings().progress
        centerline = Centerline(
            points=((10.0, 10.0), (50.0, 10.0), (50.0, 50.0), (10.0, 50.0)),
            cumulative_length_px=(0.0, 40.0, 80.0, 120.0),
            total_length_px=160.0,
        )
        estimator = ProgressSessionEstimator(
            settings=settings,
            lap_confirmer=LapTransitionConfirmer(consecutive_observations=2),
            white_lower=(0, 0, 150),
            white_upper=(180, 100, 255),
            centerline=centerline,
        )
        positions = (
            (26, 10),
            (26, 10),
            (26, 10),
            (26, 10),
            (50, 26),
            (26, 50),
            (10, 34),
            (26, 10),
        )
        laps = (8, 8, 9, 9, 9, 9, 10, 10)
        for frame, (position, lap_number) in enumerate(zip(positions, laps)):
            map_roi = np.zeros((100, 100, 3), dtype=np.uint8)
            cv2.circle(map_roi, position, 3, (0, 0, 255), -1)
            estimator.observe_frame(
                frame=frame,
                time_s=frame / 10.0,
                speed_kmh=1440.0,
                raw_lap_number=lap_number,
                map_roi=map_roi,
            )

        result = estimator.finalize()

        self.assertEqual(result.calibration.effective_lap_length_m, 160.0)
        self.assertEqual(result.frames[3].estimate.s_fused, 0.0)
        self.assertAlmostEqual(result.frames[4].estimate.s_visual, 0.25)
        self.assertEqual(result.frames[4].estimate.source, ProgressSource.FUSED)
        self.assertEqual(result.frames[7].estimate.s_fused, 0.0)

    def test_integrates_confirms_calibrates_and_returns_frame_aligned_results(self):
        settings = load_settings().progress
        estimator = ProgressSessionEstimator(
            settings=settings,
            lap_confirmer=LapTransitionConfirmer(consecutive_observations=2),
            white_lower=(0, 0, 150),
            white_upper=(180, 100, 255),
        )
        for frame, (time_s, lap_number) in enumerate(
            ((0.0, 8), (0.1, 8), (0.2, 9), (0.3, 9), (0.4, 10), (0.5, 10))
        ):
            estimator.observe_frame(
                frame=frame,
                time_s=time_s,
                speed_kmh=720.0,
                raw_lap_number=lap_number,
                map_roi=None,
            )

        result = estimator.finalize()

        self.assertEqual(len(result.frames), 6)
        self.assertEqual(result.calibration.effective_lap_length_m, 40.0)
        self.assertFalse(result.frames[0].estimate.anchored)
        self.assertIsNone(result.frames[0].estimate.s_fused)
        self.assertEqual(result.frames[3].estimate.s_fused, 0.0)
        self.assertEqual(result.frames[4].estimate.s_odometry, 0.5)
        self.assertIsNone(result.frames[4].estimate.s_fused)
        self.assertEqual(result.frames[4].estimate.source, ProgressSource.MISSING)
        self.assertEqual(result.frames[5].estimate.s_fused, 0.0)
        self.assertEqual(
            [frame.boundary.to_lap for frame in result.frames if frame.boundary],
            [9, 10],
        )


if __name__ == "__main__":
    unittest.main()
