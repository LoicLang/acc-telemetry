"""Extraction-independent contracts for longitudinal track progress."""

from dataclasses import dataclass
from enum import StrEnum


class ProgressSource(StrEnum):
    """How one longitudinal progress estimate was produced."""

    OBSERVED = "observed"
    FUSED = "fused"
    PREDICTED = "predicted"
    INTERPOLATED = "interpolated"
    MISSING = "missing"


@dataclass(frozen=True)
class ProgressEstimate:
    """Explainable longitudinal state for one frame."""

    s_fused: float | None
    s_odometry: float | None
    s_visual: float | None
    distance_m: float
    effective_lap_length_m: float | None
    uncertainty: float
    source: ProgressSource
    reasons: tuple[str, ...]
    anchored: bool

    def __post_init__(self) -> None:
        for name in ("s_fused", "s_odometry", "s_visual"):
            value = getattr(self, name)
            if value is not None and not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be in [0, 1]")
        if not 0.0 <= self.uncertainty <= 1.0:
            raise ValueError("uncertainty must be in [0, 1]")
        if not self.anchored and self.s_fused is not None:
            raise ValueError("unanchored progress cannot expose s_fused")


@dataclass(frozen=True)
class RedDotCandidate:
    """One red contour that remains plausible after basic image checks."""

    centroid: tuple[float, float]
    area_px: float
    area_fraction: float
    circularity: float


@dataclass(frozen=True)
class Centerline:
    """One ordered, resampled, closed minimap path."""

    points: tuple[tuple[float, float], ...]
    cumulative_length_px: tuple[float, ...]
    total_length_px: float


@dataclass(frozen=True)
class LapObservation:
    """Raw lap-number evidence retained independently from confirmation."""

    frame: int
    time_s: float
    raw_lap_number: int | None


@dataclass(frozen=True)
class ConfirmedLapBoundary:
    """A trusted sequential lap transition that may anchor progress."""

    frame: int
    time_s: float
    from_lap: int
    to_lap: int
    confidence: float
