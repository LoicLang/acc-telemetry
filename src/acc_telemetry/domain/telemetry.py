"""Quality-aware telemetry concepts independent of extraction libraries."""

from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import Any, Mapping


class QualityFlag(StrEnum):
    """How trustworthy and direct a normalized value is."""

    OBSERVED = "observed"
    MISSING = "missing"
    HELD = "held"
    INTERPOLATED = "interpolated"
    ANOMALOUS = "anomalous"


@dataclass(frozen=True)
class TelemetrySample:
    """One normalized instant from a video-derived ACC session."""

    frame: int
    time_s: float
    lap_number: int | None
    lap_time_s: float | None
    s: float | None
    speed_kmh: float | None
    gear: int | None
    throttle_pct: float | None
    brake_pct: float | None
    steering: float | None
    tc_active: bool | None
    abs_active: bool | None
    field_quality: Mapping[str, QualityFlag]
    anomalies: tuple[str, ...] = ()
    source_values: Mapping[str, Any] = MappingProxyType({})
