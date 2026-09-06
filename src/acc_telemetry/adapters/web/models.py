"""Pydantic models for API request/response validation."""

from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class VideoProcessRequest(BaseModel):
    """Request to process a video file."""
    video_path: str = Field(..., description="Path to the video file on the server")
    profile_name: Optional[str] = Field(
        default=None,
        description="Optional ROI profile name to force for processing",
    )


class LapMetadata(BaseModel):
    """Metadata for a single lap."""
    lap_number: int
    duration: float  # seconds
    frames: int
    avg_speed: Optional[float] = None
    max_speed: Optional[float] = None
    avg_throttle: Optional[float] = None
    avg_brake: Optional[float] = None
    lap_time: Optional[str] = None  # Formatted time string (e.g., "1:23.456")


class VideoMetadata(BaseModel):
    """Metadata for a processed video."""
    video_name: str
    video_path: str
    fps: float
    duration: float  # seconds
    frame_count: int
    total_laps: int
    laps: List[LapMetadata]
    processed_at: str  # ISO 8601 timestamp
    csv_path: str
    track_position_available: bool


class TelemetryDataPoint(BaseModel):
    """Single frame of telemetry data."""
    frame: int
    time: float
    lap_number: Optional[int] = None
    lap_time: Optional[str] = None
    track_position: Optional[float] = None
    speed: Optional[float] = None
    gear: Optional[int] = None
    model_config = ConfigDict(extra="allow", allow_inf_nan=False)
    throttle: Optional[float] = None
    brake: Optional[float] = None
    steering: Optional[float] = None
    tc_active: Optional[bool] = None
    abs_active: Optional[bool] = None
    s_odometry: Optional[float] = None
    s_visual: Optional[float] = None
    s_fused: Optional[float] = None
    s_uncertainty: Optional[float] = None
    s_source: Optional[str] = None
    s_reasons: Optional[str] = None
    quality_hint: Optional[str] = None
    field_reasons: Optional[str | dict] = None
    raw_lap_number: Optional[int] = None
    speed_raw: Optional[str | float | int] = None
    gear_raw: Optional[str | float | int] = None


class JobStatus(BaseModel):
    """Status of a background processing job."""
    job_id: str
    status: str  # "pending", "processing", "completed", "failed"
    progress: int  # 0-100
    message: str
    video_name: Optional[str] = None
    error: Optional[str] = None


class VideoListItem(BaseModel):
    """Summary of a processed video for listing."""
    video_name: str
    total_laps: int
    duration: float
    processed_at: str
    fps: float


class LapIdentifier(BaseModel):
    """Identifier for a specific lap in a session."""
    video_name: str
    lap_number: int


class ComparisonRequest(BaseModel):
    """Request to compare multiple laps."""
    laps: List[LapIdentifier] = Field(..., description="List of laps to compare (2-10 laps)")


class LapComparisonData(BaseModel):
    """Telemetry data for a single lap in comparison."""
    video_name: str
    lap_number: int
    lap_time: Optional[str] = None
    data: List[TelemetryDataPoint]
