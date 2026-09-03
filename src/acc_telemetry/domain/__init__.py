"""Telemetry concepts independent of extraction and presentation libraries."""

from .progress import (
    Centerline,
    ConfirmedLapBoundary,
    LapObservation,
    ProgressEstimate,
    ProgressSource,
    RedDotCandidate,
)

__all__ = [
    "Centerline",
    "ConfirmedLapBoundary",
    "LapObservation",
    "ProgressEstimate",
    "ProgressSource",
    "RedDotCandidate",
]
