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


if __name__ == "__main__":
    unittest.main()
