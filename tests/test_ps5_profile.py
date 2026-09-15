from pathlib import Path
import unittest

import yaml


class TestPS5Profile(unittest.TestCase):
    def test_ps5_full_map_profile_matches_twitch_with_tracking_overrides(self):
        config_path = Path(__file__).parents[1] / "config" / "roi_config.yaml"
        with config_path.open(encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)

        twitch_profile = config["twitch_720p"]
        ps5_profile = config["ps5_full_map_720p"]
        self.assertIs(ps5_profile['lap_foreground_bounds'], True)
        self.assertEqual(
            {
                key: value
                for key, value in ps5_profile.items()
                if key not in ("position_tracking", "lap_foreground_bounds")
            },
            twitch_profile,
        )
        self.assertEqual(
            ps5_profile["position_tracking"],
            {
                "white_lower": [0, 0, 150],
                "white_upper": [180, 100, 255],
                "sample_count": 60,
            },
        )

    def test_native_pedal_scale_excludes_the_nine_pixel_right_margin(self):
        import numpy as np
        from acc_telemetry.application.config import load_settings
        from acc_telemetry.extraction.controls import TelemetryExtractor

        profile = load_settings().profile('ps5_full_map_1080p')
        # Native HUD support x=1758..1901 inclusive; x=1902..1910 is outside the bar.
        # A 153px ROI used to report 144/153 = 94.1176% at full command.
        for field, color in [('throttle', (0, 255, 0)), ('brake', (0, 0, 255))]:
            for filled in (0, 36, 72, 108, 144):
                with self.subTest(field=field, filled=filled):
                    frame = np.full((1080, 1920, 3), 40, dtype=np.uint8)
                    y, height = (1005, 21) if field == 'throttle' else (1025, 18)
                    frame[y:y+height, 1758:1758+filled] = color
                    roi = profile.rois[field]
                    crop = frame[roi['y']:roi['y']+roi['height'], roi['x']:roi['x']+roi['width']]
                    observed = TelemetryExtractor(horizontal_bar_mode=profile.pedal_bar_mode).observe_frame_telemetry(
                        {field: crop}, time_s=0, visibility=(), allow_unreviewed=True)[field]
                    self.assertAlmostEqual(observed.value, filled / 144 * 100)
                    self.assertIn('hud_visibility_unverified', observed.reasons)

    def test_ps5_full_map_1080p_profile_has_calibrated_geometry(self):
        config_path = Path(__file__).parents[1] / "config" / "roi_config.yaml"
        with config_path.open(encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)

        profile = config["ps5_full_map_1080p"]
        self.assertEqual(profile['pedal_bar_mode'], 'left_connected')
        expected_rois = {
            "throttle": {"x": 1758, "y": 1005, "width": 144, "height": 21},
            "brake": {"x": 1758, "y": 1025, "width": 144, "height": 18},
            "steering": {"x": 1703, "y": 993, "width": 201, "height": 14},
            "lap_number": {"x": 356, "y": 107, "width": 71, "height": 56},
            "lap_number_training": {
                "x": 270,
                "y": 105,
                "width": 58,
                "height": 60,
            },
            "last_lap_time": {"x": 100, "y": 128, "width": 130, "height": 34},
            "speed": {"x": 1766, "y": 932, "width": 81, "height": 48},
            "gear": {"x": 1686, "y": 887, "width": 71, "height": 108},
            "track_map": {"x": 0, "y": 180, "width": 500, "height": 480},
        }

        self.assertEqual(
            {key: value for key, value in profile.items() if key not in ("position_tracking", "pedal_bar_mode")},
            expected_rois,
        )
        self.assertEqual(
            profile["position_tracking"],
            {
                "white_lower": [0, 0, 150],
                "white_upper": [180, 100, 255],
                "sample_count": 60,
            },
        )


if __name__ == "__main__":
    unittest.main()
