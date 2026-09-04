"""Tests for validated telemetry settings and component wiring."""

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

import yaml
from unittest.mock import patch

from acc_telemetry.application.config import ConfigurationError, load_settings


ROOT = Path(__file__).parents[1]


def _write_configuration(root: Path, telemetry: dict) -> None:
    config_dir = root / "config"
    config_dir.mkdir()
    (config_dir / "telemetry.yaml").write_text(yaml.safe_dump(telemetry))
    profile = {
        "throttle": {"x": 0, "y": 0, "width": 1, "height": 1},
        "brake": {"x": 0, "y": 0, "width": 1, "height": 1},
        "steering": {"x": 0, "y": 0, "width": 1, "height": 1},
    }
    (config_dir / "roi_config.yaml").write_text(
        yaml.safe_dump({"profile": profile})
    )


def _telemetry_with_progress() -> dict:
    telemetry = yaml.safe_load((ROOT / "config" / "telemetry.yaml").read_text())
    telemetry["progress"] = {
        "odometry": {
            "max_interpolation_gap_s": 0.25,
            "observed_uncertainty_per_s": 0.00005,
            "interpolated_uncertainty_per_s": 0.001,
        },
        "candidates": {
            "min_area_fraction": 0.00002,
            "max_area_fraction": 0.005,
            "min_circularity": 0.35,
            "min_compact_aspect_ratio": 0.75,
            "min_filled_extent": 0.45,
            "min_convex_compactness": 0.45,
        },
        "centerline": {
            "max_branch_length_fraction": 0.03,
            "min_cycle_diagonal_fraction": 2.0,
            "resample_spacing_diagonal_fraction": 0.0025,
        },
        "projection": {
            "max_centerline_distance_diagonal_fraction": 0.03,
            "max_progress_error": 0.04,
            "min_score_margin": 0.15,
        },
        "fusion": {
            "visual_gain": 0.35,
            "short_visual_gap_s": 0.5,
            "unavailable_uncertainty": 0.05,
        },
        "boundary_anchor": {
            "max_bracketing_gap_s": 0.25,
            "max_bracketing_distance_fraction": 0.005,
            "max_one_sided_gap_s": 0.10,
            "max_one_sided_distance_fraction": 0.002,
        },
        "lap_confirmation": {"consecutive_observations": 5},
        "calibration": {
            "max_missing_speed_fraction": 0.01,
            "max_relative_mad": 0.03,
        },
    }
    return telemetry


class TestTelemetryConfiguration(unittest.TestCase):
    def test_loads_current_ps5_profile_and_shared_thresholds(self):
        settings = load_settings(ROOT)

        profile = settings.profile("ps5_full_map_720p")
        self.assertEqual(profile.sample_count, 60)
        self.assertEqual(profile.white_lower, (0, 0, 150))
        self.assertEqual(profile.white_upper, (180, 100, 255))
        self.assertEqual(settings.position.max_jump_per_frame, 1.0)
        self.assertEqual(settings.position.frequency_threshold, 0.60)
        self.assertEqual(settings.ocr.max_speed_delta_kmh, 20)
        self.assertEqual(settings.ocr.recovery_tolerance_kmh, 3)
        self.assertEqual(settings.progress.odometry.max_interpolation_gap_s, 0.25)
        self.assertEqual(settings.progress.candidates.min_area_fraction, 0.00002)
        self.assertEqual(settings.progress.candidates.max_area_fraction, 0.005)
        self.assertEqual(settings.progress.candidates.min_circularity, 0.35)
        self.assertEqual(
            settings.progress.candidates.min_compact_aspect_ratio,
            0.75,
        )
        self.assertEqual(settings.progress.candidates.min_filled_extent, 0.45)
        self.assertEqual(
            settings.progress.candidates.min_convex_compactness,
            0.45,
        )
        self.assertEqual(settings.progress.centerline.max_branch_length_fraction, 0.03)
        self.assertEqual(settings.progress.centerline.min_cycle_diagonal_fraction, 2.0)
        self.assertEqual(settings.progress.projection.max_progress_error, 0.04)
        self.assertEqual(settings.progress.projection.min_score_margin, 0.15)
        self.assertEqual(settings.progress.fusion.visual_gain, 0.35)
        self.assertEqual(settings.progress.fusion.short_visual_gap_s, 0.5)
        self.assertEqual(
            settings.progress.boundary_anchor.max_bracketing_gap_s,
            0.25,
        )
        self.assertEqual(
            settings.progress.boundary_anchor.max_bracketing_distance_fraction,
            0.005,
        )
        self.assertEqual(
            settings.progress.boundary_anchor.max_one_sided_gap_s,
            0.10,
        )
        self.assertEqual(
            settings.progress.boundary_anchor.max_one_sided_distance_fraction,
            0.002,
        )
        self.assertEqual(settings.progress.lap_confirmation.consecutive_observations, 5)
        self.assertEqual(settings.progress.calibration.max_relative_mad, 0.03)

    def test_rejects_invalid_generic_progress_thresholds(self):
        telemetry = _telemetry_with_progress()
        invalid_cases = (
            ("progress.odometry.max_interpolation_gap_s", ("progress", "odometry", "max_interpolation_gap_s"), 0),
            ("progress.candidates.min_area_fraction", ("progress", "candidates", "min_area_fraction"), -0.1),
            ("progress.candidates.min_compact_aspect_ratio", ("progress", "candidates", "min_compact_aspect_ratio"), 0),
            ("progress.candidates.min_compact_aspect_ratio", ("progress", "candidates", "min_compact_aspect_ratio"), 1.1),
            ("progress.candidates.min_filled_extent", ("progress", "candidates", "min_filled_extent"), 0),
            ("progress.candidates.min_filled_extent", ("progress", "candidates", "min_filled_extent"), 1.1),
            ("progress.candidates.min_convex_compactness", ("progress", "candidates", "min_convex_compactness"), 0),
            ("progress.candidates.min_convex_compactness", ("progress", "candidates", "min_convex_compactness"), 1.1),
            ("progress.fusion.visual_gain", ("progress", "fusion", "visual_gain"), 1.1),
            ("progress.boundary_anchor.max_bracketing_gap_s", ("progress", "boundary_anchor", "max_bracketing_gap_s"), 0),
            ("progress.boundary_anchor.max_bracketing_gap_s", ("progress", "boundary_anchor", "max_bracketing_gap_s"), -0.1),
            ("progress.boundary_anchor.max_bracketing_distance_fraction", ("progress", "boundary_anchor", "max_bracketing_distance_fraction"), 0),
            ("progress.boundary_anchor.max_bracketing_distance_fraction", ("progress", "boundary_anchor", "max_bracketing_distance_fraction"), -0.1),
            ("progress.boundary_anchor.max_bracketing_distance_fraction", ("progress", "boundary_anchor", "max_bracketing_distance_fraction"), 1.1),
            ("progress.boundary_anchor.max_one_sided_gap_s", ("progress", "boundary_anchor", "max_one_sided_gap_s"), 0),
            ("progress.boundary_anchor.max_one_sided_gap_s", ("progress", "boundary_anchor", "max_one_sided_gap_s"), -0.1),
            ("progress.boundary_anchor.max_one_sided_distance_fraction", ("progress", "boundary_anchor", "max_one_sided_distance_fraction"), 0),
            ("progress.boundary_anchor.max_one_sided_distance_fraction", ("progress", "boundary_anchor", "max_one_sided_distance_fraction"), -0.1),
            ("progress.boundary_anchor.max_one_sided_distance_fraction", ("progress", "boundary_anchor", "max_one_sided_distance_fraction"), 1.1),
            ("progress.lap_confirmation.consecutive_observations", ("progress", "lap_confirmation", "consecutive_observations"), 0),
        )

        for expected, path, invalid in invalid_cases:
            with self.subTest(path=expected), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                changed = deepcopy(telemetry)
                target = changed
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = invalid
                _write_configuration(root, changed)
                with self.assertRaisesRegex(ConfigurationError, expected.replace(".", r"\.")):
                    load_settings(root)

    def test_rejects_one_sided_anchor_gates_larger_than_bracketing_gates(self):
        cases = (
            (
                "max_one_sided_gap_s",
                0.26,
                "progress.boundary_anchor.max_one_sided_gap_s must not exceed "
                "progress.boundary_anchor.max_bracketing_gap_s",
            ),
            (
                "max_one_sided_distance_fraction",
                0.006,
                "progress.boundary_anchor.max_one_sided_distance_fraction must not exceed "
                "progress.boundary_anchor.max_bracketing_distance_fraction",
            ),
        )

        for key, invalid, expected in cases:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as directory:
                telemetry = _telemetry_with_progress()
                telemetry["progress"]["boundary_anchor"][key] = invalid
                root = Path(directory)
                _write_configuration(root, telemetry)

                with self.assertRaisesRegex(
                    ConfigurationError,
                    expected.replace(".", r"\."),
                ):
                    load_settings(root)

    def test_rejects_overlapping_candidate_area_range(self):
        telemetry = _telemetry_with_progress()
        telemetry["progress"]["candidates"]["min_area_fraction"] = 0.005

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _write_configuration(root, telemetry)
            with self.assertRaisesRegex(ConfigurationError, "min_area_fraction"):
                load_settings(root)

    def test_loads_native_1080p_ps5_profile(self):
        profile = load_settings(ROOT).profile("ps5_full_map_1080p")

        self.assertEqual(profile.sample_count, 60)
        self.assertEqual(profile.white_lower, (0, 0, 150))
        self.assertEqual(profile.white_upper, (180, 100, 255))
        self.assertEqual(
            profile.rois["last_lap_time"],
            {"x": 100, "y": 128, "width": 130, "height": 34},
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
            telemetry = _telemetry_with_progress()
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

    @patch("acc_telemetry.application.components.ProgressSessionEstimator")
    @patch("acc_telemetry.application.components.LapTransitionConfirmer")
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
        lap_confirmer,
        progress_estimator,
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
        position_tracker.assert_not_called()
        self.assertIsNone(components.position)
        lap_confirmer.assert_called_once_with(consecutive_observations=5)
        self.assertIs(components.lap_confirmer, lap_confirmer.return_value)
        progress_estimator.assert_called_once_with(
            settings=load_settings(ROOT).progress,
            lap_confirmer=lap_confirmer.return_value,
            white_lower=(0, 0, 150),
            white_upper=(180, 100, 255),
        )
        self.assertIs(components.progress, progress_estimator.return_value)
        self.assertEqual(components.sample_count, 60)
        self.assertEqual(components.frequency_threshold, 0.60)

    @patch("acc_telemetry.application.components.ProgressSessionEstimator")
    @patch("acc_telemetry.application.components.LapTransitionConfirmer")
    @patch("acc_telemetry.application.components.PositionTrackerV2")
    @patch("acc_telemetry.application.components.LapDetector")
    @patch("acc_telemetry.application.components.TelemetryExtractor")
    @patch("acc_telemetry.application.components.VideoProcessor")
    def test_legacy_position_is_constructed_only_when_explicitly_requested(
        self,
        video_processor,
        telemetry_extractor,
        lap_detector,
        position_tracker,
        lap_confirmer,
        progress_estimator,
    ):
        from acc_telemetry.application.components import build_components

        components = build_components(
            "session.mp4",
            "ps5_full_map_720p",
            fps=30.0,
            settings=load_settings(ROOT),
            legacy_position=True,
        )

        position_tracker.assert_called_once_with(
            fps=30.0,
            max_jump_per_frame=1.0,
            white_lower=(0, 0, 150),
            white_upper=(180, 100, 255),
        )
        self.assertIs(components.position, position_tracker.return_value)


if __name__ == "__main__":
    unittest.main()
