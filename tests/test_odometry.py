"""Tests for independent speed-based longitudinal odometry."""

import unittest

from acc_telemetry.application.odometry import (
    LapDistanceSummary,
    OdometryPoint,
    SpeedObservation,
    calibrate_effective_lap_length,
    integrate_speed,
    summarize_lap_distances,
)
from acc_telemetry.domain.progress import ConfirmedLapBoundary, ProgressSource
from acc_telemetry.domain.telemetry import QualityFlag


class TestSpeedIntegration(unittest.TestCase):
    def test_integrates_constant_speed_in_metres(self):
        samples = [
            SpeedObservation(0.0, 72.0, QualityFlag.OBSERVED),
            SpeedObservation(5.0, 72.0, QualityFlag.OBSERVED),
            SpeedObservation(10.0, 72.0, QualityFlag.OBSERVED),
        ]

        trace = integrate_speed(samples, max_interpolation_gap_s=0.25)

        self.assertEqual(trace[-1].distance_m, 200.0)
        self.assertEqual(trace[-1].delta_distance_m, 100.0)
        self.assertEqual(trace[-1].source, ProgressSource.OBSERVED)

    def test_uses_trapezoidal_speed_between_observed_endpoints(self):
        samples = [
            SpeedObservation(0.0, 36.0, QualityFlag.OBSERVED),
            SpeedObservation(10.0, 72.0, QualityFlag.OBSERVED),
        ]

        trace = integrate_speed(samples, max_interpolation_gap_s=0.25)

        self.assertEqual(trace[-1].distance_m, 150.0)

    def test_does_not_integrate_duplicate_or_backward_time(self):
        samples = [
            SpeedObservation(1.0, 36.0, QualityFlag.OBSERVED),
            SpeedObservation(1.0, 36.0, QualityFlag.OBSERVED),
            SpeedObservation(0.9, 36.0, QualityFlag.OBSERVED),
        ]

        trace = integrate_speed(samples, max_interpolation_gap_s=0.25)

        self.assertEqual(trace[-1].distance_m, 0.0)
        self.assertIn("non_monotonic_time", trace[-1].reasons)

    def test_interpolates_a_bounded_internal_speed_gap(self):
        samples = [
            SpeedObservation(0.0, 36.0, QualityFlag.OBSERVED),
            SpeedObservation(0.1, None, QualityFlag.MISSING),
            SpeedObservation(0.2, 72.0, QualityFlag.OBSERVED),
        ]

        trace = integrate_speed(
            samples,
            max_interpolation_gap_s=0.25,
            observed_uncertainty_per_s=0.00005,
            interpolated_uncertainty_per_s=0.001,
        )

        self.assertAlmostEqual(trace[-1].distance_m, 3.0)
        self.assertEqual(trace[1].source, ProgressSource.INTERPOLATED)
        self.assertIn("speed_gap_interpolated", trace[1].reasons)
        self.assertGreater(trace[1].uncertainty, trace[0].uncertainty)

    def test_does_not_claim_distance_across_a_long_speed_gap(self):
        samples = [
            SpeedObservation(0.0, 36.0, QualityFlag.OBSERVED),
            SpeedObservation(0.15, None, QualityFlag.MISSING),
            SpeedObservation(0.3, 72.0, QualityFlag.OBSERVED),
        ]

        trace = integrate_speed(samples, max_interpolation_gap_s=0.25)

        self.assertEqual(trace[-1].distance_m, 0.0)
        self.assertEqual(trace[-1].source, ProgressSource.MISSING)
        self.assertIn("speed_missing", trace[-1].reasons)
        self.assertGreaterEqual(trace[-1].uncertainty, trace[1].uncertainty)

    def test_anomalous_speed_never_becomes_observed_distance(self):
        samples = [
            SpeedObservation(0.0, 36.0, QualityFlag.OBSERVED),
            SpeedObservation(0.1, 360.0, QualityFlag.ANOMALOUS),
        ]

        trace = integrate_speed(samples, max_interpolation_gap_s=0.25)

        self.assertEqual(trace[-1].distance_m, 0.0)
        self.assertEqual(trace[-1].source, ProgressSource.MISSING)
        self.assertIn("speed_anomalous", trace[-1].reasons)


class TestLapDistanceCalibration(unittest.TestCase):
    def test_summarizes_only_boundary_to_boundary_laps(self):
        trace = [
            OdometryPoint(0.0, 0.0, None, 0.0, ProgressSource.OBSERVED, ()),
            OdometryPoint(10.0, 100.0, 100.0, 0.0, ProgressSource.OBSERVED, ()),
            OdometryPoint(20.0, 220.0, 120.0, 0.0, ProgressSource.OBSERVED, ()),
        ]
        boundaries = [
            ConfirmedLapBoundary(0, 0.0, 7, 8, 1.0),
            ConfirmedLapBoundary(600, 10.0, 8, 9, 1.0),
            ConfirmedLapBoundary(1200, 20.0, 9, 10, 1.0),
        ]

        laps = summarize_lap_distances(trace, boundaries)

        self.assertEqual([lap.lap_number for lap in laps], [8, 9])
        self.assertEqual([lap.distance_m for lap in laps], [100.0, 120.0])
        self.assertTrue(all(lap.complete for lap in laps))

    def test_uses_median_and_rejects_crash_distance_outlier(self):
        laps = [
            LapDistanceSummary(number, 0.0, 100.0, distance, 0.0, True, ())
            for number, distance in enumerate((7000.0, 7010.0, 6990.0, 9100.0), 1)
        ]

        calibration = calibrate_effective_lap_length(
            laps,
            max_missing_speed_fraction=0.01,
            max_relative_mad=0.03,
        )

        self.assertEqual(calibration.effective_lap_length_m, 7000.0)
        self.assertEqual([lap.lap_number for lap in calibration.accepted_laps], [1, 2, 3])
        self.assertEqual([lap.lap_number for lap in calibration.rejected_laps], [4])
        self.assertIn("calibration_lap_rejected", calibration.rejected_laps[0].reasons)

    def test_rejects_a_duration_outlier_even_when_distance_is_similar(self):
        laps = [
            LapDistanceSummary(1, 0.0, 100.0, 7000.0, 0.0, True, ()),
            LapDistanceSummary(2, 100.0, 201.0, 7010.0, 0.0, True, ()),
            LapDistanceSummary(3, 201.0, 331.0, 7020.0, 0.0, True, ()),
        ]

        calibration = calibrate_effective_lap_length(
            laps,
            max_missing_speed_fraction=0.01,
            max_relative_mad=0.03,
        )

        self.assertEqual(
            [lap.lap_number for lap in calibration.accepted_laps],
            [1, 2],
        )
        self.assertEqual(
            [lap.lap_number for lap in calibration.rejected_laps],
            [3],
        )
        self.assertIn("duration_outlier", calibration.rejected_laps[0].reasons)

    def test_rejects_incomplete_invalid_or_speed_degraded_laps(self):
        laps = [
            LapDistanceSummary(1, 0.0, 100.0, 7000.0, 0.0, False, ("missing_boundary",)),
            LapDistanceSummary(2, 0.0, 100.0, 0.0, 0.0, True, ()),
            LapDistanceSummary(3, 0.0, 100.0, 7000.0, 0.02, True, ("speed_missing",)),
            LapDistanceSummary(4, 100.0, 100.0, 7000.0, 0.0, True, ()),
        ]

        calibration = calibrate_effective_lap_length(
            laps,
            max_missing_speed_fraction=0.01,
            max_relative_mad=0.03,
        )

        self.assertIsNone(calibration.effective_lap_length_m)
        self.assertEqual(len(calibration.accepted_laps), 0)
        self.assertEqual(len(calibration.rejected_laps), 4)
        self.assertIn("non_positive_duration", calibration.rejected_laps[-1].reasons)

    def test_single_clean_lap_has_explicit_calibration_uncertainty(self):
        calibration = calibrate_effective_lap_length(
            [LapDistanceSummary(1, 0.0, 100.0, 7000.0, 0.0, True, ())],
            max_missing_speed_fraction=0.01,
            max_relative_mad=0.03,
        )

        self.assertEqual(calibration.effective_lap_length_m, 7000.0)
        self.assertEqual(calibration.uncertainty, 0.03)


if __name__ == "__main__":
    unittest.main()
