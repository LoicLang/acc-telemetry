"""Quality-aware normalization contract tests."""

import unittest
from pathlib import Path

from acc_telemetry.application.config import load_settings
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

    def test_loads_representative_fixture(self):
        samples = load_csv_samples(FIXTURE, self.settings)

        self.assertEqual(len(samples), 8)
        self.assertEqual(samples[-1].lap_time_s, 138.123)
        self.assertEqual(samples[4].field_quality["speed_kmh"], QualityFlag.ANOMALOUS)
        self.assertEqual(samples[5].field_quality["s"], QualityFlag.ANOMALOUS)


if __name__ == "__main__":
    unittest.main()
