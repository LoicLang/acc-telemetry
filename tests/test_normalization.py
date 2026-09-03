"""Quality-aware normalization contract tests."""

import unittest
from pathlib import Path

from acc_telemetry.application.config import load_settings
from acc_telemetry.domain.progress import ProgressSource
from acc_telemetry.domain.telemetry import QualityFlag
from acc_telemetry.normalization.samples import load_csv_samples, normalize_row


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "telemetry" / "acc_ps5_representative.csv"


class TestTelemetryNormalization(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.settings = load_settings(ROOT).normalization

    def test_converts_legacy_track_position_to_normalized_s(self):
        sample = normalize_row(
            {"frame": "4", "time": "1.5", "track_position": "42.5", "speed": "171"},
            self.settings,
        )

        self.assertEqual(sample.frame, 4)
        self.assertEqual(sample.time_s, 1.5)
        self.assertEqual(sample.s, 0.425)
        self.assertEqual(sample.speed_kmh, 171.0)
        self.assertEqual(sample.field_quality["s"], QualityFlag.OBSERVED)

    def test_preserves_missing_ocr_value_with_quality(self):
        sample = normalize_row(
            {"frame": "2", "time": "0.067", "track_position": "0.2", "speed": ""},
            self.settings,
        )

        self.assertIsNone(sample.speed_kmh)
        self.assertEqual(sample.field_quality["speed_kmh"], QualityFlag.MISSING)

    def test_marks_out_of_range_speed_without_hiding_source_value(self):
        sample = normalize_row(
            {"frame": "4", "time": "0.133", "track_position": "0.4", "speed": "682"},
            self.settings,
        )

        self.assertEqual(sample.speed_kmh, 682.0)
        self.assertEqual(sample.field_quality["speed_kmh"], QualityFlag.ANOMALOUS)
        self.assertIn("speed_kmh outside [0, 400]", sample.anomalies)
        self.assertEqual(sample.source_values["speed"], "682")

    def test_applies_explicit_held_and_interpolated_hints(self):
        held = normalize_row(
            {
                "frame": "3",
                "time": "0.1",
                "track_position": "0.2",
                "speed": "63",
                "quality_hint": "s:held;speed_kmh:held",
            },
            self.settings,
        )
        interpolated = normalize_row(
            {
                "frame": "6",
                "time": "0.2",
                "track_position": "0.6",
                "speed": "66",
                "quality_hint": "s:interpolated",
            },
            self.settings,
        )

        self.assertEqual(held.field_quality["s"], QualityFlag.HELD)
        self.assertEqual(held.field_quality["speed_kmh"], QualityFlag.HELD)
        self.assertEqual(interpolated.field_quality["s"], QualityFlag.INTERPOLATED)

    def test_prefers_fused_progress_and_preserves_component_evidence(self):
        sample = normalize_row(
            {
                "frame": "12",
                "time": "0.2",
                "track_position": "10.35",
                "s_odometry": "0.1",
                "s_visual": "0.11",
                "s_fused": "0.1035",
                "s_uncertainty": "0.002",
                "s_source": "fused",
                "s_reasons": "visual_correction;speed_gap_interpolated",
            },
            self.settings,
        )

        self.assertEqual(sample.s, 0.1035)
        self.assertEqual(sample.s_odometry, 0.1)
        self.assertEqual(sample.s_visual, 0.11)
        self.assertEqual(sample.s_uncertainty, 0.002)
        self.assertEqual(sample.s_source, ProgressSource.FUSED)
        self.assertEqual(
            sample.s_reasons,
            ("visual_correction", "speed_gap_interpolated"),
        )
        self.assertEqual(sample.field_quality["s"], QualityFlag.FUSED)
        self.assertEqual(sample.source_values["track_position"], "10.35")

    def test_missing_modern_progress_does_not_fall_back_to_legacy_saturation(self):
        sample = normalize_row(
            {
                "frame": "12",
                "time": "0.2",
                "track_position": "100.0",
                "s_fused": "",
                "s_source": "missing",
                "s_reasons": "uncertainty_limit",
            },
            self.settings,
        )

        self.assertIsNone(sample.s)
        self.assertEqual(sample.s_source, ProgressSource.MISSING)
        self.assertEqual(sample.field_quality["s"], QualityFlag.MISSING)
        self.assertEqual(sample.s_reasons, ("uncertainty_limit",))

    def test_old_row_remains_legacy_observed_progress(self):
        sample = normalize_row(
            {"frame": "4", "time": "1.5", "track_position": "42.5"},
            self.settings,
        )

        self.assertEqual(sample.s, 0.425)
        self.assertIsNone(sample.s_source)
        self.assertEqual(sample.field_quality["s"], QualityFlag.OBSERVED)

    def test_loads_representative_fixture(self):
        samples = load_csv_samples(FIXTURE, self.settings)

        self.assertEqual(len(samples), 8)
        self.assertEqual(samples[-1].lap_time_s, 138.123)
        self.assertEqual(samples[4].field_quality["speed_kmh"], QualityFlag.ANOMALOUS)
        self.assertEqual(samples[5].field_quality["s"], QualityFlag.ANOMALOUS)


if __name__ == "__main__":
    unittest.main()
