from pathlib import Path
import inspect
import tempfile
import unittest
from unittest.mock import patch

import yaml
from fastapi import BackgroundTasks

from src.web.api import videos
from src.web.models import VideoProcessRequest
from src.web.services.processing import VideoProcessingService


class TestWebProfileSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        config_path = Path(__file__).parents[1] / "config" / "roi_config.yaml"
        with config_path.open(encoding="utf-8") as config_file:
            cls.full_config = yaml.safe_load(config_file)

    def setUp(self):
        self.service = VideoProcessingService()

    def test_process_video_signature_accepts_optional_profile_name(self):
        parameters = inspect.signature(VideoProcessingService.process_video).parameters

        self.assertIn("profile_name", parameters)
        self.assertIsNone(parameters["profile_name"].default)

    def test_upload_endpoint_signature_exposes_optional_profile_name(self):
        parameters = inspect.signature(videos.upload_video).parameters

        self.assertIn("profile_name", parameters)
        self.assertIsNone(parameters["profile_name"].default.default)

    def test_select_roi_profile_returns_explicit_ps5_profile(self):
        profile = self.service._select_roi_profile(
            self.full_config,
            profile_name="ps5_full_map_720p",
        )

        self.assertEqual(profile, self.full_config["ps5_full_map_720p"])

    def test_select_roi_profile_preserves_legacy_overlay_behavior(self):
        overlay_profile = self.service._select_roi_profile(
            self.full_config,
            has_overlay=True,
        )
        default_profile = self.service._select_roi_profile(
            self.full_config,
            has_overlay=False,
        )

        self.assertEqual(overlay_profile, self.full_config["go_setups_720p"])
        self.assertEqual(default_profile, self.full_config["twitch_720p"])

    def test_select_roi_profile_rejects_unknown_profile_with_available_profiles(self):
        with self.assertRaises(ValueError) as context:
            self.service._select_roi_profile(
                self.full_config,
                profile_name="unknown_profile",
            )

        message = str(context.exception)
        self.assertIn("unknown_profile", message)
        self.assertIn("go_setups_720p", message)
        self.assertIn("ps5_full_map_720p", message)
        self.assertIn("twitch_720p", message)

    def test_video_process_request_accepts_profile_name(self):
        request = VideoProcessRequest(
            video_path="/tmp/session.mp4",
            profile_name="ps5_full_map_720p",
        )

        self.assertEqual(request.profile_name, "ps5_full_map_720p")


class TestWebProfileSelectionApi(unittest.IsolatedAsyncioTestCase):
    async def test_process_endpoint_passes_profile_name_to_processing_service(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "session.mp4"
            video_path.write_bytes(b"fake video contents")

            request = VideoProcessRequest(
                video_path=str(video_path),
                profile_name="ps5_full_map_720p",
            )
            background_tasks = BackgroundTasks()
            captured = {}

            async def fake_process_video(
                video_path: str,
                video_name: str,
                has_overlay: bool = False,
                profile_name: str | None = None,
                progress_callback=None,
            ):
                captured["video_path"] = video_path
                captured["video_name"] = video_name
                captured["has_overlay"] = has_overlay
                captured["profile_name"] = profile_name
                captured["progress_callback"] = progress_callback
                return None

            with (
                patch.object(videos.storage, "video_exists", return_value=False),
                patch.object(videos.job_manager, "create_job", return_value="job-123"),
                patch.object(videos.job_manager, "update_job"),
                patch.object(videos.job_manager, "complete_job"),
                patch.object(videos.job_manager, "fail_job"),
                patch.object(videos.processing, "process_video", side_effect=fake_process_video),
            ):
                response = await videos.process_video(request, background_tasks)

                self.assertEqual(response["job_id"], "job-123")
                self.assertEqual(len(background_tasks.tasks), 1)

                await background_tasks()

            self.assertEqual(captured["video_path"], str(video_path))
            self.assertEqual(captured["video_name"], "session")
            self.assertFalse(captured["has_overlay"])
            self.assertEqual(captured["profile_name"], "ps5_full_map_720p")
            self.assertIsNotNone(captured["progress_callback"])


if __name__ == "__main__":
    unittest.main()
