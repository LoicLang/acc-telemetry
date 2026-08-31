"""Tests for shared telemetry orchestration."""

import unittest

from acc_telemetry.application.pipeline import TelemetryPipeline


class FakeVideo:
    def __init__(self):
        self.current_frame = object()
        self.closed = False

    def open_video(self):
        return True

    def get_video_info(self):
        return {"fps": 30.0, "frame_count": 1, "duration": 1 / 30}

    def process_frames(self):
        yield 0, 0.0, {"throttle": object(), "brake": object(), "steering": object()}

    def close(self):
        self.closed = True


class FakeControls:
    def extract_frame_telemetry(self, roi_dict):
        return {
            "throttle": 50.0,
            "brake": 0.0,
            "steering": 0.1,
            "tc_active": 0,
            "abs_active": 0,
        }


class FakeLaps:
    def extract_lap_number(self, frame):
        return 9

    def extract_speed(self, frame):
        return 171

    def extract_gear(self, frame):
        return 4

    def detect_lap_transition(self, lap_number, previous_lap):
        return False

    def finalize_lap_detection(self):
        return None


class FakePosition:
    def is_ready(self):
        return False

    def reset_for_new_lap(self):
        raise AssertionError("no transition expected")


class TestTelemetryPipeline(unittest.TestCase):
    def test_extracts_one_stable_legacy_record_and_reports_progress(self):
        video = FakeVideo()
        progress = []
        pipeline = TelemetryPipeline(
            video=video,
            controls=FakeControls(),
            laps=FakeLaps(),
            position=FakePosition(),
            has_track_map=False,
            progress_callback=lambda percent, message: progress.append((percent, message)),
        )

        result = pipeline.run()

        self.assertEqual(result.video_info["frame_count"], 1)
        self.assertEqual(result.records, [{
            "frame": 0,
            "time": 0.0,
            "lap_number": 9,
            "lap_time": None,
            "track_position": None,
            "speed": 171,
            "gear": 4,
            "throttle": 50.0,
            "brake": 0.0,
            "steering": 0.1,
            "tc_active": 0,
            "abs_active": 0,
        }])
        self.assertTrue(video.closed)
        self.assertEqual(progress[0][0], 5)
        self.assertEqual(progress[-1][0], 85)

    def test_closes_video_when_extraction_fails(self):
        video = FakeVideo()

        class BrokenControls(FakeControls):
            def extract_frame_telemetry(self, roi_dict):
                raise RuntimeError("bad frame")

        pipeline = TelemetryPipeline(
            video=video,
            controls=BrokenControls(),
            laps=FakeLaps(),
            position=FakePosition(),
            has_track_map=False,
        )

        with self.assertRaisesRegex(RuntimeError, "bad frame"):
            pipeline.run()
        self.assertTrue(video.closed)


if __name__ == "__main__":
    unittest.main()
