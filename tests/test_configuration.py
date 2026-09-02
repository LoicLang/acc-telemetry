"""Tests for validated telemetry settings and component wiring."""

import tempfile
import unittest
from pathlib import Path

import yaml
from unittest.mock import patch

from acc_telemetry.application.config import ConfigurationError, load_settings


ROOT = Path(__file__).parents[1]


class TestTelemetryConfiguration(unittest.TestCase):
    def test_loads_current_ps5_profile_and_shared_thresholds(self):
        settings = load_settings(ROOT)

        profile = settings.profile("ps5_full_map_720p")
        self.assertEqual(profile.sample_count, 60)
        self.assertEqual(profile.white_lower, (0, 0, 150))
        self.assertEqual(profile.white_upper, (180, 100, 255))
        self.assertEqual(settings.position.max_jump_per_frame, 1.0)
        self.assertEqual(settings.position.frequency_threshold, 0.45)
        self.assertEqual(settings.ocr.max_speed_delta_kmh, 20)
        self.assertEqual(settings.ocr.recovery_tolerance_kmh, 3)

    def test_loads_native_1080p_ps5_profile(self):
        profile = load_settings(ROOT).profile("ps5_full_map_1080p")

        self.assertEqual(profile.sample_count, 60)
        self.assertEqual(profile.white_lower, (0, 0, 150))
        self.assertEqual(profile.white_upper, (180, 100, 255))
        self.assertEqual(
            profile.rois["last_lap_time"],
            {"x": 90, "y": 125, "width": 155, "height": 40},
        )

    def test_rejects_missing_required_settings_section(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir()
            (root / "config" / "telemetry.yaml").write_text("ocr: {}\n")
            (root / "config" / "roi_config.yaml").write_text("profile: {}\n")

            with self.assertRaisesRegex(ConfigurationError, "position"):
                load_settings(root)

    def test_rejects_out_of_range_hsv_profile(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config_dir = root / "config"
            config_dir.mkdir()
            telemetry = {
                "position": {"frequency_threshold": 0.45, "max_jump_per_frame": 1.0},
                "ocr": {"max_speed_delta_kmh": 20, "recovery_tolerance_kmh": 3},
                "normalization": {
                    "speed_min_kmh": 0,
                    "speed_max_kmh": 400,
                    "pedal_min_percent": 0,
                    "pedal_max_percent": 100,
                },
            }
            (config_dir / "telemetry.yaml").write_text(yaml.safe_dump(telemetry))
            profile = {
                "throttle": {"x": 0, "y": 0, "width": 1, "height": 1},
                "brake": {"x": 0, "y": 0, "width": 1, "height": 1},
                "steering": {"x": 0, "y": 0, "width": 1, "height": 1},
                "position_tracking": {
                    "white_lower": [0, 0, 300],
                    "white_upper": [180, 100, 255],
                    "sample_count": 10,
                },
            }
            (config_dir / "roi_config.yaml").write_text(yaml.safe_dump({"profile": profile}))

            with self.assertRaisesRegex(ConfigurationError, "white_lower"):
                load_settings(root)

    @patch("acc_telemetry.application.components.PositionTrackerV2")
    @patch("acc_telemetry.application.components.LapDetector")
    @patch("acc_telemetry.application.components.TelemetryExtractor")
    @patch("acc_telemetry.application.components.VideoProcessor")
    def test_component_factory_wires_validated_thresholds(
        self,
        video_processor,
        telemetry_extractor,
        lap_detector,
        position_tracker,
    ):
        from acc_telemetry.application.components import build_components

        components = build_components(
            "session.mp4",
            "ps5_full_map_720p",
            fps=30.0,
            settings=load_settings(ROOT),
        )

        video_processor.assert_called_once()
        self.assertIn("speed", video_processor.call_args.args[1])
        telemetry_extractor.assert_called_once_with()
        lap_detector.assert_called_once()
        detector = lap_detector.return_value
        self.assertEqual(detector._max_speed_ocr_delta_kmh, 20)
        self.assertEqual(detector._speed_ocr_recovery_tolerance_kmh, 3)
        position_tracker.assert_called_once_with(
            fps=30.0,
            max_jump_per_frame=1.0,
            white_lower=(0, 0, 150),
            white_upper=(180, 100, 255),
        )
        self.assertEqual(components.sample_count, 60)
        self.assertEqual(components.frequency_threshold, 0.45)


if __name__ == "__main__":
    unittest.main()
