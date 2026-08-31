"""Shared sequential telemetry extraction use case."""

from dataclasses import dataclass
from typing import Any, Callable

import cv2

from acc_telemetry.extraction.video import evenly_spaced_frame_indices


ProgressCallback = Callable[[int, str], None]


@dataclass(frozen=True)
class PipelineResult:
    records: list[dict[str, Any]]
    video_info: dict[str, Any]
    lap_transitions: list[dict[str, Any]]


class TelemetryPipeline:
    """Coordinate extraction without owning CLI, web, or output concerns."""

    def __init__(
        self,
        *,
        video: Any,
        controls: Any,
        laps: Any,
        position: Any,
        has_track_map: bool,
        sample_count: int = 11,
        frequency_threshold: float | None = None,
        progress_callback: ProgressCallback | None = None,
    ):
        self.video = video
        self.controls = controls
        self.laps = laps
        self.position = position
        self.has_track_map = has_track_map
        self.sample_count = sample_count
        self.frequency_threshold = frequency_threshold
        self.progress_callback = progress_callback

    def _progress(self, percent: int, message: str) -> None:
        if self.progress_callback is not None:
            self.progress_callback(percent, message)

    def _extract_track_path(self, video_info: dict[str, Any]) -> None:
        self._progress(10, "Extracting track path from minimap...")
        map_rois = []
        for frame_number in evenly_spaced_frame_indices(
            video_info["frame_count"], self.sample_count
        ):
            self.video.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            read, frame = self.video.cap.read()
            if read:
                map_rois.append(self.video.extract_roi(frame, "track_map"))
        self.video.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

        if self.frequency_threshold is None:
            extracted = self.position.extract_track_path(map_rois)
        else:
            extracted = self.position.extract_track_path(
                map_rois,
                frequency_threshold=self.frequency_threshold,
            )
        message = (
            "Track path extraction successful"
            if extracted
            else "Warning: Track path extraction failed"
        )
        self._progress(15, message)

    def run(self) -> PipelineResult:
        """Open, process, and close one video, returning legacy-compatible records."""
        try:
            if not self.video.open_video():
                raise ValueError("Could not open video file")
            video_info = self.video.get_video_info()
            self._progress(5, "Video opened successfully")

            if self.has_track_map:
                self._extract_track_path(video_info)

            self._progress(20, "Processing frames and extracting telemetry...")
            records: list[dict[str, Any]] = []
            previous_lap = None
            transitions: list[dict[str, Any]] = []
            completed_lap_times: dict[int, str] = {}
            frames_since_transition = 0
            last_progress = 20
            total_frames = max(int(video_info["frame_count"]), 1)

            for frame_number, timestamp, rois in self.video.process_frames():
                controls = self.controls.extract_frame_telemetry(rois)
                lap_number = self.laps.extract_lap_number(self.video.current_frame)
                speed = self.laps.extract_speed(self.video.current_frame)
                gear = self.laps.extract_gear(self.video.current_frame)

                track_position = None
                if "track_map" in rois and self.position.is_ready():
                    track_position = self.position.extract_position(rois["track_map"])

                if self.laps.detect_lap_transition(lap_number, previous_lap):
                    frames_since_transition = 1
                    self.position.reset_for_new_lap()
                    if "track_map" in rois and self.position.is_ready():
                        track_position = self.position.extract_position(rois["track_map"])
                    transitions.append({
                        "frame": frame_number,
                        "time": timestamp,
                        "from_lap": previous_lap,
                        "to_lap": lap_number,
                        "completed_lap_time": None,
                    })
                elif frames_since_transition == 1:
                    completed_lap_time = self.laps.extract_last_lap_time(
                        self.video.current_frame
                    )
                    if completed_lap_time and previous_lap is not None:
                        completed_lap_times[previous_lap] = completed_lap_time
                        if transitions:
                            transitions[-1]["completed_lap_time"] = completed_lap_time
                    frames_since_transition = 0

                records.append({
                    "frame": frame_number,
                    "time": timestamp,
                    "lap_number": lap_number,
                    "lap_time": None,
                    "track_position": track_position,
                    "speed": speed,
                    "gear": gear,
                    "throttle": controls["throttle"],
                    "brake": controls["brake"],
                    "steering": controls["steering"],
                    "tc_active": controls["tc_active"],
                    "abs_active": controls["abs_active"],
                })
                previous_lap = lap_number

                current_progress = 20 + int((frame_number / total_frames) * 60)
                if current_progress > last_progress and current_progress % 5 == 0:
                    self._progress(
                        current_progress,
                        f"Processing frames: {frame_number}/{total_frames}",
                    )
                    last_progress = current_progress

            final_lap = self.laps.finalize_lap_detection()
            if final_lap is not None and (previous_lap is None or final_lap > previous_lap):
                if previous_lap is not None and final_lap == previous_lap + 1:
                    for record in reversed(records):
                        if record["lap_number"] == previous_lap:
                            record["lap_number"] = final_lap
                        else:
                            break

            for record in records:
                record["lap_time"] = completed_lap_times.get(record["lap_number"])

            self._progress(85, "Generating outputs...")
            return PipelineResult(records, video_info, transitions)
        finally:
            self.video.close()
