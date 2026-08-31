import io
from pathlib import Path
import inspect
import tempfile
import unittest
from unittest.mock import patch

import yaml
from fastapi import HTTPException
from fastapi import BackgroundTasks, UploadFile
from starlette.datastructures import Headers

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

    def test_validate_profile_name_normalizes_blank_and_trims_known_profiles(self):
        self.assertIsNone(self.service.validate_profile_name(None))
        self.assertIsNone(self.service.validate_profile_name("   "))
        self.assertEqual(
            self.service.validate_profile_name("  ps5_full_map_720p  "),
            "ps5_full_map_720p",
        )

    def test_video_process_request_accepts_profile_name(self):
        request = VideoProcessRequest(
            video_path="/tmp/session.mp4",
            profile_name="ps5_full_map_720p",
        )

        self.assertEqual(request.profile_name, "ps5_full_map_720p")


class TestWebProfileSelectionApi(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        config_path = Path(__file__).parents[1] / "config" / "roi_config.yaml"
        with config_path.open(encoding="utf-8") as config_file:
            cls.full_config = yaml.safe_load(config_file)

    def setUp(self):
        self.service = VideoProcessingService()

    async def test_process_video_keeps_fourth_positional_argument_as_progress_callback(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "session.mp4"
            video_path.write_bytes(b"fake video contents")
            callback_updates = []

            def progress_callback(progress: int, message: str):
                callback_updates.append((progress, message))

            class FakeProcessor:
                def __init__(self, video_path, roi_config):
                    self.video_path = video_path
                    self.roi_config = roi_config
                    self.current_frame = object()
                    self.cap = self

                def open_video(self):
                    return True

                def get_video_info(self):
                    return {"fps": 60.0, "duration": 1.0, "frame_count": 1}

                def process_frames(self):
                    return iter(())

                def set(self, prop_id, value):
                    return None

                def read(self):
                    return False, None

                def close(self):
                    return None

            class FakeVisualizer:
                def __init__(self, output_dir: str):
                    self.output_dir = output_dir

                def create_dataframe(self, telemetry_data):
                    return telemetry_data

                def export_csv(self, df, filename: str):
                    return str(Path(temp_dir) / filename)

                def generate_summary(self, df):
                    return {
                        "laps": [],
                        "total_laps": 0,
                        "track_position_tracked": False,
                    }

            class FakeExtractor:
                def extract_frame_telemetry(self, roi_dict):
                    return {
                        "throttle": 0.0,
                        "brake": 0.0,
                        "steering": 0.0,
                        "tc_active": False,
                        "abs_active": False,
                    }

            class FakeLapDetector:
                def __init__(self, roi_config, enable_performance_stats: bool = False):
                    self.roi_config = roi_config

                def extract_lap_number(self, current_frame):
                    return None

                def extract_speed(self, current_frame):
                    return None

                def extract_gear(self, current_frame):
                    return None

                def detect_lap_transition(self, lap_number, previous_lap):
                    return False

                def finalize_lap_detection(self):
                    return None

            class FakePositionTracker:
                def __init__(self, white_lower=None, white_upper=None):
                    self.white_lower = white_lower
                    self.white_upper = white_upper

                def extract_track_path(self, map_rois):
                    return False

                def is_ready(self):
                    return False

                def reset_for_new_lap(self):
                    return None

                def extract_position(self, track_map):
                    return None

            with (
                patch.object(self.service, "load_roi_config", return_value=self.full_config),
                patch("src.web.services.processing.VideoProcessor", FakeProcessor),
                patch("src.web.services.processing.TelemetryExtractor", FakeExtractor),
                patch("src.web.services.processing.LapDetector", FakeLapDetector),
                patch("src.web.services.processing.PositionTrackerV2", FakePositionTracker),
                patch("src.web.services.processing.InteractiveTelemetryVisualizer", FakeVisualizer),
                patch.object(self.service.storage, "get_video_directory", return_value=Path(temp_dir)),
                patch.object(self.service.storage, "save_metadata"),
            ):
                metadata = await self.service.process_video(
                    str(video_path),
                    "session",
                    False,
                    progress_callback,
                )

            self.assertEqual(metadata.video_name, "session")
            self.assertEqual(callback_updates[0], (5, "Video opened successfully"))
            self.assertEqual(callback_updates[-1], (100, "Processing complete!"))

    async def test_process_video_accepts_profile_name_as_fifth_positional_argument(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "session.mp4"
            video_path.write_bytes(b"fake video contents")
            callback_updates = []
            processor_configs = []

            def progress_callback(progress: int, message: str):
                callback_updates.append((progress, message))

            class FakeProcessor:
                def __init__(self, video_path, roi_config):
                    self.video_path = video_path
                    self.roi_config = roi_config
                    self.current_frame = object()
                    self.cap = self
                    processor_configs.append(roi_config)

                def open_video(self):
                    return True

                def get_video_info(self):
                    return {"fps": 60.0, "duration": 1.0, "frame_count": 1}

                def process_frames(self):
                    return iter(())

                def set(self, prop_id, value):
                    return None

                def read(self):
                    return False, None

                def close(self):
                    return None

            class FakeVisualizer:
                def __init__(self, output_dir: str):
                    self.output_dir = output_dir

                def create_dataframe(self, telemetry_data):
                    return telemetry_data

                def export_csv(self, df, filename: str):
                    return str(Path(temp_dir) / filename)

                def generate_summary(self, df):
                    return {
                        "laps": [],
                        "total_laps": 0,
                        "track_position_tracked": False,
                    }

            class FakeExtractor:
                def extract_frame_telemetry(self, roi_dict):
                    return {
                        "throttle": 0.0,
                        "brake": 0.0,
                        "steering": 0.0,
                        "tc_active": False,
                        "abs_active": False,
                    }

            class FakeLapDetector:
                def __init__(self, roi_config, enable_performance_stats: bool = False):
                    self.roi_config = roi_config

                def extract_lap_number(self, current_frame):
                    return None

                def extract_speed(self, current_frame):
                    return None

                def extract_gear(self, current_frame):
                    return None

                def detect_lap_transition(self, lap_number, previous_lap):
                    return False

                def finalize_lap_detection(self):
                    return None

            class FakePositionTracker:
                def __init__(self, white_lower=None, white_upper=None):
                    self.white_lower = white_lower
                    self.white_upper = white_upper

                def extract_track_path(self, map_rois):
                    return False

                def is_ready(self):
                    return False

                def reset_for_new_lap(self):
                    return None

                def extract_position(self, track_map):
                    return None

            with (
                patch.object(self.service, "load_roi_config", return_value=self.full_config),
                patch("src.web.services.processing.VideoProcessor", FakeProcessor),
                patch("src.web.services.processing.TelemetryExtractor", FakeExtractor),
                patch("src.web.services.processing.LapDetector", FakeLapDetector),
                patch("src.web.services.processing.PositionTrackerV2", FakePositionTracker),
                patch("src.web.services.processing.InteractiveTelemetryVisualizer", FakeVisualizer),
                patch.object(self.service.storage, "get_video_directory", return_value=Path(temp_dir)),
                patch.object(self.service.storage, "save_metadata"),
            ):
                metadata = await self.service.process_video(
                    str(video_path),
                    "session",
                    False,
                    progress_callback,
                    "ps5_full_map_720p",
                )

            self.assertEqual(metadata.video_name, "session")
            self.assertEqual(processor_configs, [self.full_config["ps5_full_map_720p"]])
            self.assertEqual(callback_updates[0], (5, "Video opened successfully"))
            self.assertEqual(callback_updates[-1], (100, "Processing complete!"))

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

    async def test_process_endpoint_rejects_unknown_profile_before_creating_job(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            video_path = Path(temp_dir) / "session.mp4"
            video_path.write_bytes(b"fake video contents")

            request = VideoProcessRequest(
                video_path=str(video_path),
                profile_name="unknown_profile",
            )
            background_tasks = BackgroundTasks()

            with (
                patch.object(videos.storage, "video_exists", return_value=False),
                patch.object(videos.job_manager, "create_job") as create_job,
            ):
                with self.assertRaises(HTTPException) as context:
                    await videos.process_video(request, background_tasks)

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("Unknown ROI profile", context.exception.detail)
            create_job.assert_not_called()
            self.assertEqual(len(background_tasks.tasks), 0)

    async def test_upload_endpoint_passes_profile_name_to_processing_service(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            saved_video_path = Path(temp_dir) / "session.mp4"
            background_tasks = BackgroundTasks()
            captured = {}
            upload = UploadFile(
                file=io.BytesIO(b"fake video contents"),
                filename="session.mp4",
                headers=Headers({"content-type": "video/mp4"}),
            )

            class FakeCapture:
                def isOpened(self):
                    return True

                def get(self, prop_id):
                    return 720

                def release(self):
                    return None

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
                patch.object(videos.storage, "get_video_path", return_value=saved_video_path),
                patch.object(videos.storage, "video_exists", return_value=False),
                patch.object(videos.job_manager, "create_job", return_value="job-456"),
                patch.object(videos.job_manager, "update_job"),
                patch.object(videos.job_manager, "complete_job"),
                patch.object(videos.job_manager, "fail_job"),
                patch.object(videos.cv2, "VideoCapture", return_value=FakeCapture()),
                patch.object(videos.processing, "process_video", side_effect=fake_process_video),
            ):
                response = await videos.upload_video(
                    file=upload,
                    has_overlay=False,
                    profile_name="ps5_full_map_720p",
                    background_tasks=background_tasks,
                )

                self.assertEqual(response.video_name, "session")
                self.assertEqual(response.video_path, str(saved_video_path))
                self.assertEqual(len(background_tasks.tasks), 1)

                await background_tasks()

            self.assertTrue(saved_video_path.exists())
            self.assertEqual(captured["video_path"], str(saved_video_path))
            self.assertEqual(captured["video_name"], "session")
            self.assertFalse(captured["has_overlay"])
            self.assertEqual(captured["profile_name"], "ps5_full_map_720p")
            self.assertIsNotNone(captured["progress_callback"])

    async def test_upload_endpoint_rejects_unknown_profile_before_writing_file_or_creating_job(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            saved_video_path = Path(temp_dir) / "session.mp4"
            background_tasks = BackgroundTasks()
            upload = UploadFile(
                file=io.BytesIO(b"fake video contents"),
                filename="session.mp4",
                headers=Headers({"content-type": "video/mp4"}),
            )

            class FakeCapture:
                def isOpened(self):
                    return True

                def get(self, prop_id):
                    return 720

                def release(self):
                    return None

            with (
                patch.object(videos.storage, "get_video_path", return_value=saved_video_path),
                patch.object(videos.storage, "video_exists", return_value=False),
                patch.object(videos.job_manager, "create_job") as create_job,
                patch.object(videos.cv2, "VideoCapture", return_value=FakeCapture()),
            ):
                with self.assertRaises(HTTPException) as context:
                    await videos.upload_video(
                        file=upload,
                        has_overlay=False,
                        profile_name="unknown_profile",
                        background_tasks=background_tasks,
                    )

            self.assertEqual(context.exception.status_code, 400)
            self.assertIn("Unknown ROI profile", context.exception.detail)
            create_job.assert_not_called()
            self.assertFalse(saved_video_path.exists())
            self.assertEqual(len(background_tasks.tasks), 0)


if __name__ == "__main__":
    unittest.main()
