"""Shared sequential telemetry extraction use case."""

from dataclasses import dataclass
from typing import Any, Callable

import cv2

from acc_telemetry.domain.telemetry import QualityFlag
from acc_telemetry.extraction.video import evenly_spaced_frame_indices


ProgressCallback = Callable[[int, str], None]
PositionDiagnosticCallback = Callable[[dict[str, Any]], None]


@dataclass(frozen=True)
class PipelineResult:
    records: list[dict[str, Any]]
    video_info: dict[str, Any]
    lap_transitions: list[dict[str, Any]]
    progress_calibration: Any | None = None


class TelemetryPipeline:
    """Coordinate extraction without owning CLI, web, or output concerns."""

    def __init__(
        self,
        *,
        video: Any,
        controls: Any,
        laps: Any,
        position: Any | None = None,
        progress: Any | None = None,
        has_track_map: bool,
        sample_count: int = 11,
        frequency_threshold: float | None = None,
        progress_callback: ProgressCallback | None = None,
        position_diagnostic_callback: PositionDiagnosticCallback | None = None,
    ):
        self.video = video
        self.controls = controls
        self.laps = laps
        self.position = position
        self.progress = progress
        self.has_track_map = has_track_map
        self.sample_count = sample_count
        self.frequency_threshold = frequency_threshold
        self.progress_callback = progress_callback
        self.position_diagnostic_callback = position_diagnostic_callback

    def _progress(self, percent: int, message: str) -> None:
        if self.progress_callback is not None:
            self.progress_callback(percent, message)

    def _report_position_diagnostic(
        self,
        *,
        frame_number: int,
        timestamp: float,
        lap_number: int | None,
        track_position: float,
    ) -> None:
        if self.position_diagnostic_callback is None:
            return
        diagnostic = self.position.get_last_position_diagnostic()
        dot_x = diagnostic.dot_position[0] if diagnostic.dot_position else None
        dot_y = diagnostic.dot_position[1] if diagnostic.dot_position else None
        self.position_diagnostic_callback({
            "frame": frame_number,
            "time": timestamp,
            "lap_number": lap_number,
            "track_position": track_position,
            "dot_x": dot_x,
            "dot_y": dot_y,
            "closest_idx": diagnostic.closest_idx,
            "start_idx": diagnostic.start_idx,
            "start_source": diagnostic.start_source,
            "travel_direction": diagnostic.travel_direction,
            "raw_position": diagnostic.raw_position,
            "completion_forced": diagnostic.completion_forced,
            "validated_position": diagnostic.validated_position,
            "decision": diagnostic.decision.value,
        })

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

        if self.progress is not None:
            extracted = self.progress.prepare_map(
                map_rois,
                frequency_threshold=self.frequency_threshold,
            )
        elif self.frequency_threshold is None:
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

    def _report_generic_progress(self, frame_result: Any, *, time_s: float) -> None:
        if self.position_diagnostic_callback is None:
            return
        estimate = frame_result.estimate
        selected = frame_result.selected_centroid
        self.position_diagnostic_callback({
            "frame": frame_result.frame,
            "time": time_s,
            "raw_lap_number": frame_result.raw_lap_number,
            "confirmed_lap_number": frame_result.confirmed_lap_number,
            "boundary_confidence": frame_result.boundary_confidence,
            "boundary_confirmed": frame_result.boundary is not None,
            "boundary_anchor_source": (
                None
                if frame_result.boundary_anchor_source is None
                else frame_result.boundary_anchor_source.value
            ),
            "candidate_count": frame_result.candidate_count,
            "selected_x": None if selected is None else selected[0],
            "selected_y": None if selected is None else selected[1],
            "track_position": (
                None if estimate.s_fused is None else estimate.s_fused * 100.0
            ),
            "s_odometry": estimate.s_odometry,
            "s_visual": estimate.s_visual,
            "s_fused": estimate.s_fused,
            "distance_m": estimate.distance_m,
            "effective_lap_length_m": estimate.effective_lap_length_m,
            "uncertainty": estimate.uncertainty,
            "source": estimate.source.value,
            "reasons": ";".join(estimate.reasons),
            "anchored": estimate.anchored,
        })

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
                speed_quality = (
                    self.laps.get_last_speed_quality()
                    if hasattr(self.laps, "get_last_speed_quality")
                    else (
                        QualityFlag.OBSERVED
                        if speed is not None
                        else QualityFlag.MISSING
                    )
                )
                gear = self.laps.extract_gear(self.video.current_frame)

                track_position = None
                if self.progress is not None:
                    self.progress.observe_frame(
                        frame=frame_number,
                        time_s=timestamp,
                        speed_kmh=speed,
                        speed_quality=speed_quality,
                        raw_lap_number=lap_number,
                        map_roi=rois.get("track_map"),
                    )
                elif "track_map" in rois and self.position.is_ready():
                    track_position = self.position.extract_position(rois["track_map"])

                if self.progress is None and self.laps.detect_lap_transition(lap_number, previous_lap):
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

                if track_position is not None:
                    self._report_position_diagnostic(
                        frame_number=frame_number,
                        timestamp=timestamp,
                        lap_number=lap_number,
                        track_position=track_position,
                    )

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

            if self.progress is not None:
                progress_result = self.progress.finalize()
                if len(progress_result.frames) != len(records):
                    raise ValueError("Progress result is not frame-aligned")
                transitions = []
                for record, frame_result in zip(records, progress_result.frames):
                    estimate = frame_result.estimate
                    record["lap_number"] = frame_result.confirmed_lap_number
                    record["track_position"] = (
                        None if estimate.s_fused is None else estimate.s_fused * 100.0
                    )
                    record["s_odometry"] = estimate.s_odometry
                    record["s_visual"] = estimate.s_visual
                    record["s_fused"] = estimate.s_fused
                    record["s_uncertainty"] = estimate.uncertainty
                    record["s_source"] = estimate.source.value
                    record["s_reasons"] = ";".join(estimate.reasons)
                    if frame_result.boundary is not None:
                        boundary = frame_result.boundary
                        transitions.append({
                            "frame": boundary.frame,
                            "time": boundary.time_s,
                            "from_lap": boundary.from_lap,
                            "to_lap": boundary.to_lap,
                            "completed_lap_time": None,
                        })
                    self._report_generic_progress(
                        frame_result,
                        time_s=record["time"],
                    )

            self._progress(85, "Generating outputs...")
            return PipelineResult(
                records,
                video_info,
                transitions,
                (
                    progress_result.calibration
                    if self.progress is not None
                    else None
                ),
            )
        finally:
            self.video.close()
