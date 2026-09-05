"""Extraction-independent evidence for one measured field."""
from dataclasses import dataclass
from typing import Generic, TypeVar

from acc_telemetry.domain.telemetry import QualityFlag

T = TypeVar("T")


@dataclass(frozen=True)
class FieldObservation(Generic[T]):
    value: T | None
    quality: QualityFlag
    raw_value: str | float | int | bool | None
    reasons: tuple[str, ...] = ()
    last_observed_time_s: float | None = None
