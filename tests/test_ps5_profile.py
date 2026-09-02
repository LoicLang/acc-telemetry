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
        self.assertEqual(
            {
                key: value
                for key, value in ps5_profile.items()
                if key != "position_tracking"
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

    def test_ps5_full_map_1080p_profile_has_calibrated_geometry(self):
        config_path = Path(__file__).parents[1] / "config" / "roi_config.yaml"
        with config_path.open(encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)

        profile = config["ps5_full_map_1080p"]
        expected_rois = {
            "throttle": {"x": 1758, "y": 1005, "width": 153, "height": 21},
            "brake": {"x": 1758, "y": 1025, "width": 153, "height": 18},
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
            "track_map": {"x": 5, "y": 323, "width": 404, "height": 275},
        }

        self.assertEqual(
            {key: value for key, value in profile.items() if key != "position_tracking"},
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
