"""Read reviewed control visibility; actual video bounds are checked by pipeline."""
import json
from pathlib import Path

from acc_telemetry.domain.observations import VisibilitySpan, validate_visibility


def load_visibility(path: Path | str | None) -> tuple[VisibilitySpan, ...]:
    if path is None:
        return ()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("visibility JSON must be an array of reviewed spans")
    try:
        spans = tuple(VisibilitySpan(**row) for row in data)
        duration = max((s.end_s for s in spans), default=0)
        return validate_visibility(spans, duration_s=duration)
    except (TypeError, AttributeError) as error:
        raise ValueError("invalid visibility JSON span") from error
