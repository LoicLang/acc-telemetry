"""Video processing service for telemetry extraction."""

import yaml
from pathlib import Path
from typing import Callable, Dict, Optional
from datetime import datetime

from acc_telemetry.extraction.video import VideoProcessor
from acc_telemetry.extraction.controls import TelemetryExtractor
from acc_telemetry.extraction.laps import LapDetector
from acc_telemetry.visualization.interactive import InteractiveTelemetryVisualizer
from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.application.session_artifacts import (
    check_destination, source_identity, write_session_artifacts,
)
from acc_telemetry.application.visibility import load_visibility
from acc_telemetry.application.speed_visibility import load_speed_visibility
from acc_telemetry.application.config import load_settings
from acc_telemetry.application.lap_state import LapTransitionConfirmer
from acc_telemetry.application.progress import ProgressSessionEstimator

from ..config import settings
from ..models import VideoMetadata, LapMetadata
from .storage import StorageService


class VideoProcessingService:
    """Handles video processing and telemetry extraction."""

    def __init__(self):
        self.storage = StorageService()
        self.config_path = settings.roi_config_path

    def load_roi_config(self) -> dict:
        """Load ROI configuration from YAML file."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def _build_progress_estimator(
        self,
        profile_name: str,
    ) -> ProgressSessionEstimator:
        """Build the same generic progress engine used by the packaged CLI."""
        telemetry_settings = load_settings()
        profile = telemetry_settings.profile(profile_name)
        confirmer = LapTransitionConfirmer(
            consecutive_observations=(
                telemetry_settings.progress.lap_confirmation.consecutive_observations
            )
        )
        return ProgressSessionEstimator(
            settings=telemetry_settings.progress,
            lap_confirmer=confirmer,
            white_lower=profile.white_lower,
            white_upper=profile.white_upper,
        )

    async def process_video(
        self,
        video_path: str,
        video_name: str,
        has_overlay: bool = False,
        progress_callback: Optional[Callable[[int, str], None]] = None,
        profile_name: Optional[str] = None,
        visibility_json: Optional[str] = None,
        speed_visibility_json: Optional[str] = None,
        artifact_dir: Optional[str] = None,
        clip_origin: Optional[dict] = None,
    ) -> VideoMetadata:
        """
        Process a video and extract telemetry data.

        Args:
            video_path: Path to the video file
            video_name: Sanitized name for output directory
            progress_callback: Optional callback for progress updates (percentage, message)

        Returns:
            VideoMetadata object

        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video cannot be opened
        """
        video_path_obj = Path(video_path)

        if not video_path_obj.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        source_before = None
        if artifact_dir is not None:
            target = check_destination(artifact_dir, video_path)
            reports = self.storage.get_video_directory(video_name).resolve()
            if target == reports or target in reports.parents:
                raise ValueError("legacy reports must remain outside the artifact directory")
            source_before = source_identity(video_path)
        telemetry_settings = load_settings()

        # Load configuration
        full_config = self.load_roi_config()
        profile_name = self.validate_profile_name(profile_name, full_config=full_config)
        active_profile_name = profile_name or (
            'go_setups_720p' if has_overlay else 'twitch_720p'
        )
        roi_config = self._select_roi_profile(
            full_config,
            profile_name=profile_name,
            has_overlay=has_overlay,
        )

        # Initialize components
        processor = VideoProcessor(video_path, roi_config)
        extractor = TelemetryExtractor()

        lap_roi_config = roi_config.copy()
        if 'lap_number_training' in roi_config:
            lap_roi_config['lap_number'] = roi_config['lap_number_training']

        lap_detector = LapDetector(lap_roi_config, enable_performance_stats=False)
        lap_detector._max_speed_ocr_delta_kmh = telemetry_settings.ocr.max_speed_delta_kmh
        lap_detector._speed_ocr_recovery_tolerance_kmh = telemetry_settings.ocr.recovery_tolerance_kmh
        lap_detector._lap_foreground_margin_px = telemetry_settings.ocr.lap_foreground_margin_px
        lap_detector._lap_foreground_bounds = telemetry_settings.profile(active_profile_name).lap_foreground_bounds
        position_config = roi_config.get('position_tracking', {})
        progress_estimator = self._build_progress_estimator(active_profile_name)

        pipeline = TelemetryPipeline(
            settings=telemetry_settings,
            visibility=load_visibility(visibility_json),
            speed_visibility=load_speed_visibility(speed_visibility_json),
            video=processor,
            controls=extractor,
            laps=lap_detector,
            progress=progress_estimator,
            has_track_map='track_map' in roi_config,
            sample_count=int(position_config.get('sample_count', 11)),
            frequency_threshold=load_settings().position.frequency_threshold,
            progress_callback=progress_callback,
        )
        result = pipeline.run()
        if artifact_dir is not None:
            write_session_artifacts(result, artifact_dir, source_path=video_path,
                source_before=source_before, profile=active_profile_name, clip_origin=clip_origin)

        visualizer = InteractiveTelemetryVisualizer(
            output_dir=str(self.storage.get_video_directory(video_name))
        )
        df = visualizer.create_dataframe(result.records)
        csv_path = visualizer.export_csv(df, filename="telemetry.csv")

        if progress_callback:
            progress_callback(90, "Generating metadata...")
        summary = visualizer.generate_summary(df)
        metadata = self._create_metadata(
            video_name=video_name,
            video_path=video_path,
            video_info=result.video_info,
            summary=summary,
            csv_path=csv_path,
        )
        self.storage.save_metadata(video_name, metadata)
        if progress_callback:
            progress_callback(100, "Processing complete!")
        return metadata

    def validate_profile_name(
        self,
        profile_name: Optional[str],
        full_config: Optional[Dict] = None,
    ) -> Optional[str]:
        """Normalize profile names and reject unknown configured profiles."""
        if profile_name is None:
            return None

        normalized_profile_name = profile_name.strip()
        if not normalized_profile_name:
            return None

        if full_config is None:
            full_config = self.load_roi_config()

        if normalized_profile_name not in full_config:
            available_profiles = ", ".join(sorted(full_config))
            raise ValueError(
                f"Unknown ROI profile '{normalized_profile_name}'. "
                f"Available profiles: {available_profiles}"
            )

        return normalized_profile_name

    def _select_roi_profile(
        self,
        full_config: Dict,
        profile_name: Optional[str] = None,
        has_overlay: bool = False,
    ) -> Dict:
        """Select the ROI profile from config without side effects."""
        if profile_name is not None:
            roi_config = full_config.get(profile_name)
            if roi_config is None:
                available_profiles = ", ".join(sorted(full_config))
                raise ValueError(
                    f"Unknown ROI profile '{profile_name}'. "
                    f"Available profiles: {available_profiles}"
                )
            return roi_config

        legacy_profile_name = 'go_setups_720p' if has_overlay else 'twitch_720p'
        roi_config = full_config.get(legacy_profile_name)
        if roi_config:
            return roi_config

        if full_config:
            return next(iter(full_config.values()))

        raise ValueError("No ROI profiles are configured.")

    def _create_metadata(
        self,
        video_name: str,
        video_path: str,
        video_info: Dict,
        summary: Dict,
        csv_path: str
    ) -> VideoMetadata:
        """
        Create VideoMetadata object from processing results.

        Args:
            video_name: Sanitized video name
            video_path: Original video path
            video_info: Video information dict
            summary: Summary statistics dict
            csv_path: Path to CSV file

        Returns:
            VideoMetadata object
        """
        # Create lap metadata
        laps = []
        for lap_info in summary.get('laps', []):
            laps.append(LapMetadata(
                lap_number=lap_info['lap_number'],
                duration=lap_info['duration'],
                frames=lap_info['frames'],
                avg_speed=lap_info.get('avg_speed'),
                max_speed=lap_info.get('max_speed'),
                avg_throttle=lap_info.get('avg_throttle'),
                avg_brake=lap_info.get('avg_brake'),
                lap_time=None  # Will be filled if available
            ))

        return VideoMetadata(
            video_name=video_name,
            video_path=video_path,
            fps=video_info['fps'],
            duration=video_info['duration'],
            frame_count=video_info['frame_count'],
            total_laps=summary.get('total_laps', 0),
            laps=laps,
            processed_at=datetime.now().isoformat(),
            csv_path=csv_path,
            track_position_available=summary.get('track_position_tracked', False)
        )
