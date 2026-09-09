"""Source-bound reviewed speed HUD visibility; no automatic image classification."""
from dataclasses import dataclass
import json
import math
from pathlib import Path
import re

from .session_artifacts import source_identity


@dataclass(frozen=True)
class SpeedVisibilitySpan:
    start_s: float
    end_s: float
    state: str
    reviewer: str


@dataclass(frozen=True)
class SpeedVisibilityReview:
    source_sha256: str
    source_size_bytes: int
    spans: tuple[SpeedVisibilitySpan, ...]

    def validate(self, *, duration_s: float | None = None) -> None:
        if (not isinstance(self.source_sha256, str)
                or re.fullmatch(r'[0-9a-f]{64}', self.source_sha256) is None
                or type(self.source_size_bytes) is not int or self.source_size_bytes <= 0):
            raise ValueError('invalid speed visibility source identity')
        previous_end = 0.0
        for span in self.spans:
            if (not isinstance(span, SpeedVisibilitySpan)
                    or any(isinstance(t, bool) or not isinstance(t, (float, int))
                           or not math.isfinite(t) for t in (span.start_s, span.end_s))
                    or not previous_end <= span.start_s < span.end_s
                    or span.state not in ('visible', 'absent', 'unknown')
                    or not isinstance(span.reviewer, str) or not span.reviewer.strip()
                    or (duration_s is not None and span.end_s > duration_s)):
                raise ValueError('invalid or overlapping speed visibility span')
            previous_end = span.end_s

    def verify_source(self, path, *, duration_s: float) -> None:
        if not math.isfinite(duration_s) or duration_s < 0:
            raise ValueError('invalid speed visibility duration')
        self.validate(duration_s=duration_s)
        if path is None:
            raise ValueError('speed visibility requires a source video path')
        actual = source_identity(path)
        if (actual['sha256'] != self.source_sha256
                or actual['size_bytes'] != self.source_size_bytes):
            raise ValueError('speed visibility does not match source video')

    def state_at(self, time_s: float) -> str:
        span = self.span_at(time_s)
        return span.state if span is not None else 'unknown'

    def span_at(self, time_s: float) -> SpeedVisibilitySpan | None:
        return next((span for span in self.spans
                     if span.start_s <= time_s < span.end_s), None)


def load_speed_visibility(path: Path | str | None) -> SpeedVisibilityReview | None:
    if path is None:
        return None
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(data, dict) or data.get('schema_version') != 'speed-visibility-v1':
        raise ValueError('speed visibility requires a source-bound v1 review')
    if set(data) != {'schema_version', 'source_sha256', 'source_size_bytes', 'spans'}:
        raise ValueError('invalid speed visibility review fields')
    try:
        review = SpeedVisibilityReview(data['source_sha256'], data['source_size_bytes'],
            tuple(SpeedVisibilitySpan(**row) for row in data['spans']))
        review.validate()
    except (TypeError, KeyError, AttributeError) as error:
        raise ValueError('invalid speed visibility review') from error
    return review
