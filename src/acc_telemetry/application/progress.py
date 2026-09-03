"""Pure temporal selection and fusion for generic longitudinal progress."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from acc_telemetry.domain.progress import ProgressSource
from acc_telemetry.extraction.map_progress import VisualProjection


@dataclass(frozen=True)
class VisualSelection:
    """The accepted visual correction or an explicit rejection."""

    s_visual: float | None
    centroid: tuple[float, float] | None
    score: float | None
    uncertainty: float
    source: ProgressSource
    reasons: tuple[str, ...]


def wrapped_delta(value: float, reference: float) -> float:
    """Return value-reference on the normalized interval (-0.5, 0.5]."""
    delta = (value - reference) % 1.0
    return delta - 1.0 if delta > 0.5 else delta


def select_visual_projection(
    projections: tuple[VisualProjection, ...],
    *,
    predicted_s: float,
    current_uncertainty: float,
    last_centroid: tuple[float, float] | None,
    previous_displacement_px: float | None,
    speed_kmh: float | None,
    delta_time_s: float,
    roi_diagonal_px: float,
    max_centerline_distance_diagonal_fraction: float,
    max_progress_error: float,
    min_score_margin: float,
) -> VisualSelection:
    """Choose visual evidence only when one temporally plausible option wins."""
    if not projections:
        return VisualSelection(
            None,
            None,
            None,
            min(1.0, current_uncertainty),
            ProgressSource.MISSING,
            ("visual_missing",),
        )

    distance_gate = (
        roi_diagonal_px * max_centerline_distance_diagonal_fraction
    )
    progress_gate = min(0.5, max_progress_error + current_uncertainty)
    displacement_gate = max(
        distance_gate,
        2.0 * (previous_displacement_px or 0.0),
    )
    stationary = speed_kmh is not None and speed_kmh <= 1.0
    invalid_time = delta_time_s <= 0
    scored: list[tuple[float, VisualProjection]] = []

    for projection in projections:
        progress_error = abs(wrapped_delta(projection.s_visual, predicted_s))
        if (
            projection.distance_px > distance_gate
            or progress_error > progress_gate
        ):
            continue
        if last_centroid is None:
            displacement = 0.0
        else:
            displacement = hypot(
                projection.centroid[0] - last_centroid[0],
                projection.centroid[1] - last_centroid[1],
            )
            if (stationary or invalid_time) and displacement > distance_gate:
                continue
        score = (
            0.40 * progress_error / progress_gate
            + 0.30 * projection.distance_px / distance_gate
            + 0.30 * displacement / displacement_gate
        )
        scored.append((score, projection))

    if not scored:
        return VisualSelection(
            None,
            None,
            None,
            min(1.0, current_uncertainty),
            ProgressSource.MISSING,
            ("visual_out_of_gate",),
        )

    scored.sort(
        key=lambda item: (
            item[0],
            item[1].s_visual,
            item[1].centroid[1],
            item[1].centroid[0],
        )
    )
    best_score, best = scored[0]
    if len(scored) > 1 and scored[1][0] - best_score < min_score_margin:
        return VisualSelection(
            None,
            None,
            None,
            min(1.0, current_uncertainty),
            ProgressSource.MISSING,
            ("visual_ambiguous",),
        )

    return VisualSelection(
        s_visual=best.s_visual,
        centroid=best.centroid,
        score=best_score,
        uncertainty=min(1.0, current_uncertainty + best_score * 0.01),
        source=ProgressSource.OBSERVED,
        reasons=("visual_selected",),
    )
