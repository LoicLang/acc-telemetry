"""Tests for shared telemetry orchestration."""

import unittest

from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.application.progress import (
    BoundaryAnchorSource,
    ProgressFrameResult,
    ProgressSessionResult,
)
from acc_telemetry.domain.progress import ProgressEstimate, ProgressSource
from acc_telemetry.domain.telemetry import QualityFlag
from acc_telemetry.domain.observations import FieldObservation
from acc_telemetry.extraction.position import PositionDecision, PositionDiagnostic


class FakeVideo:
    def __init__(self):
        self.current_frame = object()
        self.closed = False

    def open_video(self):
        return True

    def get_video_info(self):
        return {"fps": 30.0, "frame_count": 1, "duration": 1 / 30}

    def process_frames(self):
        yield 0, 0.0, {
            "throttle": object(),
            "brake": object(),
            "steering": object(),
            "track_map": object(),
        }

    def close(self):
        self.closed = True


class FakeControls:
    def observe_frame_telemetry(self, rois, *, time_s, visibility):
        return {k: FieldObservation(v, QualityFlag.OBSERVED, v)
                for k, v in self.extract_frame_telemetry(rois).items()}

    def extract_frame_telemetry(self, roi_dict):
        return {
            "throttle": 50.0,
            "brake": 0.0,
            "steering": 0.1,
            "tc_active": 0,
            "abs_active": 0,
        }


class FakeLaps:
    def observe_speed(self, frame):
        return FieldObservation(171, QualityFlag.OBSERVED, "171")

    def observe_gear(self, frame):
        return FieldObservation(4, QualityFlag.OBSERVED, "4")

    def observe_lap_number(self, frame):
        return FieldObservation(9, QualityFlag.OBSERVED, "9")

    def extract_lap_number(self, frame):
        return 9

    def extract_speed(self, frame):
        return 171

    def get_last_speed_quality(self):
        return QualityFlag.OBSERVED

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


class ReadyPosition(FakePosition):
    def is_ready(self):
        return True

    def extract_position(self, roi):
        return 42.0

    def get_last_position_diagnostic(self):
        return PositionDiagnostic(
            dot_position=(12, 34),
            closest_idx=56,
            start_idx=7,
            start_source="geometric",
            travel_direction=1,
            raw_position=42.5,
            completion_forced=False,
            validated_position=42.0,
            decision=PositionDecision.SMOOTHED,
        )


class FakeGenericProgress:
    def __init__(self):
        self.observations = []
        self.finalized = False

    def observe_frame(self, **observation):
        self.observations.append(observation)

    def finalize(self):
        self.finalized = True
        return ProgressSessionResult(
            frames=(
                ProgressFrameResult(
                    frame=0,
                    raw_lap_number=9,
                    confirmed_lap_number=9,
                    boundary=None,
                    boundary_confidence=1.0,
                    candidate_count=2,
                    selected_centroid=(12.0, 34.0),
                    estimate=ProgressEstimate(
                        s_fused=0.1035,
                        s_odometry=0.10,
                        s_visual=0.11,
                        distance_m=100.0,
                        effective_lap_length_m=1000.0,
                        uncertainty=0.002,
                        source=ProgressSource.FUSED,
                        reasons=("visual_correction",),
                        anchored=True,
                    ),
                    boundary_anchor_source=BoundaryAnchorSource.EXACT,
                ),
            ),
            calibration=None,
        )


class TestTelemetryPipeline(unittest.TestCase):
    def test_applies_generic_progress_only_after_collecting_frame_observations(self):
        generic_progress = FakeGenericProgress()
        diagnostics = []
        pipeline = TelemetryPipeline(
            video=FakeVideo(),
            controls=FakeControls(),
            laps=FakeLaps(),
            position=FakePosition(),
            progress=generic_progress,
            has_track_map=False,
            position_diagnostic_callback=diagnostics.append,
        )

        result = pipeline.run()

        self.assertTrue(generic_progress.finalized)
        self.assertEqual(len(generic_progress.observations), 1)
        self.assertEqual(generic_progress.observations[0]["speed_kmh"], 171)
        self.assertEqual(
            generic_progress.observations[0]["speed_quality"],
            QualityFlag.OBSERVED,
        )
        self.assertEqual(generic_progress.observations[0]["raw_lap_number"], 9)
        self.assertEqual(result.records[0]["track_position"], 10.35)
        self.assertEqual(result.records[0]["s_odometry"], 0.10)
        self.assertEqual(result.records[0]["s_visual"], 0.11)
        self.assertEqual(result.records[0]["s_fused"], 0.1035)
        self.assertEqual(result.records[0]["s_uncertainty"], 0.002)
        self.assertEqual(result.records[0]["s_source"], "fused")
        self.assertEqual(result.records[0]["s_reasons"], "visual_correction")
        self.assertNotIn("boundary_anchor_source", result.records[0])
        self.assertEqual(diagnostics[0]["candidate_count"], 2)
        self.assertEqual(diagnostics[0]["selected_x"], 12.0)
        self.assertEqual(diagnostics[0]["confirmed_lap_number"], 9)
        self.assertEqual(
            diagnostics[0]["boundary_anchor_source"],
            "boundary_anchor_exact",
        )

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

    def test_reports_position_diagnostic_without_changing_legacy_record(self):
        diagnostics = []
        pipeline = TelemetryPipeline(
            video=FakeVideo(),
            controls=FakeControls(),
            laps=FakeLaps(),
            position=ReadyPosition(),
            has_track_map=False,
            position_diagnostic_callback=diagnostics.append,
        )

        result = pipeline.run()

        self.assertEqual(result.records[0]["track_position"], 42.0)
        self.assertNotIn("raw_position", result.records[0])
        self.assertEqual(
            diagnostics,
            [{
                "frame": 0,
                "time": 0.0,
                "lap_number": 9,
                "track_position": 42.0,
                "dot_x": 12,
                "dot_y": 34,
                "closest_idx": 56,
                "start_idx": 7,
                "start_source": "geometric",
                "travel_direction": 1,
                "raw_position": 42.5,
                "completion_forced": False,
                "validated_position": 42.0,
                "decision": "smoothed",
            }],
        )


if __name__ == "__main__":
    unittest.main()
