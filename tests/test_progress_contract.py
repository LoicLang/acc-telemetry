"""Tests for extraction-independent longitudinal progress contracts."""

import unittest

from acc_telemetry.domain.progress import (
    Centerline,
    ConfirmedLapBoundary,
    LapObservation,
    ProgressEstimate,
    ProgressSource,
    RedDotCandidate,
)


class TestProgressContract(unittest.TestCase):
    def test_constructs_all_public_progress_evidence(self):
        candidate = RedDotCandidate(
            centroid=(12.5, 24.5),
            area_px=160.0,
            area_fraction=0.001,
            circularity=0.9,
        )
        centerline = Centerline(
            points=((0.0, 0.0), (1.0, 0.0)),
            cumulative_length_px=(0.0, 1.0),
            total_length_px=2.0,
        )
        observation = LapObservation(frame=60, time_s=1.0, raw_lap_number=8)
        boundary = ConfirmedLapBoundary(
            frame=120,
            time_s=2.0,
            from_lap=8,
            to_lap=9,
            confidence=1.0,
        )
        estimate = ProgressEstimate(
            s_fused=0.25,
            s_odometry=0.24,
            s_visual=0.26,
            distance_m=125.0,
            effective_lap_length_m=500.0,
            uncertainty=0.01,
            source=ProgressSource.FUSED,
            reasons=("visual_correction",),
            anchored=True,
        )

        self.assertEqual(candidate.centroid, (12.5, 24.5))
        self.assertEqual(centerline.total_length_px, 2.0)
        self.assertEqual(observation.raw_lap_number, 8)
        self.assertEqual(boundary.to_lap, 9)
        self.assertEqual(estimate.s_fused, 0.25)

    def test_rejects_progress_values_outside_normalized_range(self):
        values = {
            "s_fused": 0.1,
            "s_odometry": 0.1,
            "s_visual": 0.1,
            "distance_m": 1.0,
            "effective_lap_length_m": 10.0,
            "uncertainty": 0.1,
            "source": ProgressSource.FUSED,
            "reasons": (),
            "anchored": True,
        }

        for field, invalid in (
            ("s_fused", 1.01),
            ("s_odometry", -0.01),
            ("s_visual", 2.0),
            ("uncertainty", -0.1),
        ):
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, field):
                ProgressEstimate(**(values | {field: invalid}))

    def test_unanchored_progress_cannot_expose_fused_s(self):
        with self.assertRaisesRegex(ValueError, "unanchored"):
            ProgressEstimate(
                s_fused=0.1,
                s_odometry=0.1,
                s_visual=None,
                distance_m=1.0,
                effective_lap_length_m=10.0,
                uncertainty=0.1,
                source=ProgressSource.PREDICTED,
                reasons=("unanchored",),
                anchored=False,
            )


if __name__ == "__main__":
    unittest.main()
