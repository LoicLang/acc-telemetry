"""Shared construction of configured extraction components."""

from dataclasses import dataclass
from pathlib import Path
from acc_telemetry.domain.observations import VisibilitySpan
from .visibility import load_visibility

from acc_telemetry.extraction.controls import TelemetryExtractor
from acc_telemetry.extraction.laps import LapDetector
from acc_telemetry.extraction.position import PositionTrackerV2
from acc_telemetry.extraction.video import VideoProcessor

from .config import TelemetrySettings, load_settings
from .lap_state import LapTransitionConfirmer
from .progress import ProgressSessionEstimator


@dataclass(frozen=True)
class ProcessingComponents:
    video: VideoProcessor
    controls: TelemetryExtractor
    laps: LapDetector
    lap_confirmer: LapTransitionConfirmer
    progress: ProgressSessionEstimator
    position: PositionTrackerV2 | None
    profile_name: str
    sample_count: int
    frequency_threshold: float
    visibility: tuple[VisibilitySpan, ...] = ()


def build_components(
    video_path: str,
    profile_name: str,
    *,
    fps: float = 30.0,
    enable_performance_stats: bool = False,
    settings: TelemetrySettings | None = None,
    legacy_position: bool = False,
    visibility_json: Path | str | None = None,
) -> ProcessingComponents:
    """Build every extraction component from one validated settings object."""
    visibility = load_visibility(visibility_json)
    active_settings = settings or load_settings()
    profile = active_settings.profile(profile_name)
    roi_config = {name: dict(coordinates) for name, coordinates in profile.rois.items()}

    lap_roi_config = dict(roi_config)
    if "lap_number_training" in lap_roi_config:
        lap_roi_config["lap_number"] = lap_roi_config["lap_number_training"]

    video = VideoProcessor(video_path, roi_config)
    controls = TelemetryExtractor()
    laps = LapDetector(
        lap_roi_config,
        enable_performance_stats=enable_performance_stats,
    )
    laps._max_speed_ocr_delta_kmh = active_settings.ocr.max_speed_delta_kmh
    laps._speed_ocr_recovery_tolerance_kmh = active_settings.ocr.recovery_tolerance_kmh
    position = (
        PositionTrackerV2(
            fps=fps,
            max_jump_per_frame=active_settings.position.max_jump_per_frame,
            white_lower=profile.white_lower,
            white_upper=profile.white_upper,
        )
        if legacy_position
        else None
    )
    lap_confirmer = LapTransitionConfirmer(
        consecutive_observations=(
            active_settings.progress.lap_confirmation.consecutive_observations
        )
    )
    progress = ProgressSessionEstimator(
        settings=active_settings.progress,
        lap_confirmer=lap_confirmer,
        white_lower=profile.white_lower,
        white_upper=profile.white_upper,
    )

    return ProcessingComponents(
        visibility=visibility,
        video=video,
        controls=controls,
        laps=laps,
        lap_confirmer=lap_confirmer,
        progress=progress,
        position=position,
        profile_name=profile_name,
        sample_count=profile.sample_count,
        frequency_threshold=active_settings.position.frequency_threshold,
    )
