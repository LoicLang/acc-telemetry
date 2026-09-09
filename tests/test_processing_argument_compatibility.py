"""Existing positional artifact arguments must not become visibility input."""
import inspect
import unittest
from acc_telemetry.adapters.web.services.processing import VideoProcessingService


class TestProcessingArgumentCompatibility(unittest.TestCase):
    def test_existing_positional_artifact_and_origin_keep_their_meaning(self):
        origin = {'source_id': 'parent', 'start_s': 12.5}
        call = inspect.signature(VideoProcessingService.process_video).bind(
            None, 'video.mov', 'session', False, None, 'ps5_full_map_1080p',
            None, 'artifact-directory', origin)
        self.assertEqual(call.arguments['artifact_dir'], 'artifact-directory')
        self.assertEqual(call.arguments['clip_origin'], origin)
        self.assertNotIn('speed_visibility_json', call.arguments)
