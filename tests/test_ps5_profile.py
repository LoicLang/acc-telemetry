from pathlib import Path
import unittest

import yaml


class TestPS5Profile(unittest.TestCase):
    def test_ps5_full_map_profile(self):
        config_path = Path(__file__).parents[1] / "config" / "roi_config.yaml"
        with config_path.open(encoding="utf-8") as config_file:
            profile = yaml.safe_load(config_file)["ps5_full_map_720p"]

        self.assertEqual(
            profile["track_map"],
            {"x": 3, "y": 215, "width": 269, "height": 183},
        )
        self.assertEqual(profile["position_tracking"]["white_lower"], [0, 0, 150])
        self.assertEqual(profile["position_tracking"]["white_upper"], [180, 100, 255])
        self.assertEqual(profile["position_tracking"]["sample_count"], 60)


if __name__ == "__main__":
    unittest.main()
