"""Extraction-independent evidence for one measured field."""
import math
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


@dataclass(frozen=True)
class VisibilitySpan:
    """Reviewed visible interval [start_s, end_s), in video-relative seconds."""
    field: str
    start_s: float
    end_s: float
    reviewer: str


def validate_visibility(spans, *, duration_s: float) -> tuple[VisibilitySpan, ...]:
    """Reject malformed, unsorted or overlapping same-field review intervals."""
    if not math.isfinite(duration_s) or duration_s < 0:
        raise ValueError("invalid visibility video duration")
    spans = tuple(spans)
    last_start = -1.0
    ends = {}
    for span in spans:
        if (span.field not in ("throttle", "brake", "steering")
            or not isinstance(span.reviewer, str) or not span.reviewer.strip()
            or isinstance(span.start_s, bool) or isinstance(span.end_s, bool)
            or not isinstance(span.start_s, (int, float))
            or not isinstance(span.end_s, (int, float))
            or not math.isfinite(span.start_s) or not math.isfinite(span.end_s)
            or not 0 <= span.start_s < span.end_s <= duration_s):
            raise ValueError("invalid visibility span")
        if span.start_s < last_start or span.start_s < ends.get(span.field, 0):
            raise ValueError("visibility spans must be sorted and non-overlapping per field")
        last_start = span.start_s
        ends[span.field] = span.end_s
    return spans


def visible_at(spans, field: str, time_s: float) -> bool:
    return any(s.field == field and s.start_s <= time_s < s.end_s for s in spans)
