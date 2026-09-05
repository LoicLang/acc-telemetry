"""Pure temporal selection and fusion for generic longitudinal progress."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import hypot, isclose

import numpy as np

from acc_telemetry.application.odometry import (
    LapLengthCalibration,
    OdometryPoint,
    SpeedObservation,
    calibrate_effective_lap_length,
    integrate_speed,
    summarize_lap_distances,
)
from acc_telemetry.application.config import BoundaryAnchorSettings, ProgressSettings
from acc_telemetry.application.lap_state import LapState, LapTransitionConfirmer
from acc_telemetry.domain.progress import (
    ConfirmedLapBoundary,
    ProgressEstimate,
    ProgressSource,
)
from acc_telemetry.domain.telemetry import QualityFlag
from acc_telemetry.extraction.map_progress import (
    CenterlineTopologyError,
    VisualProjection,
    build_centerline,
    build_white_probability,
    extract_red_candidates,
    project_candidate,
)
from acc_telemetry.domain.progress import Centerline, LapObservation, RedDotCandidate


@dataclass(frozen=True)
class VisualSelection:
    """The accepted visual correction or an explicit rejection."""

    s_visual: float | None
    centroid: tuple[float, float] | None
    score: float | None
    uncertainty: float
    source: ProgressSource
    reasons: tuple[str, ...]


class BoundaryAnchorSource(StrEnum):
    EXACT = "boundary_anchor_exact"
    INTERPOLATED = "boundary_anchor_interpolated"
    NEAREST = "boundary_anchor_nearest"
    MISSING = "boundary_anchor_missing"


@dataclass(frozen=True)
class AnchorFrameEvidence:
    time_s: float
    distance_m: float
    projections: tuple[VisualProjection, ...]
    boundary: ConfirmedLapBoundary | None


@dataclass(frozen=True)
class BoundaryVisualAnchor:
    raw_s: float | None
    centroid: tuple[float, float] | None
    uncertainty: float
    source: BoundaryAnchorSource


@dataclass(frozen=True)
class ProgressReplayObservation:
    """Ready-to-fuse evidence retained for offline replay."""

    odometry: OdometryPoint
    visual: VisualSelection
    boundary: ConfirmedLapBoundary | None


@dataclass(frozen=True)
class ProgressReplayResult:
    """Offline fused trace plus its learned lap-length evidence."""

    estimates: tuple[ProgressEstimate, ...]
    calibration: LapLengthCalibration


@dataclass(frozen=True)
class ProgressFrameResult:
    """Final generic progress and lap evidence aligned to one source frame."""

    frame: int
    raw_lap_number: int | None
    confirmed_lap_number: int | None
    boundary: ConfirmedLapBoundary | None
    boundary_confidence: float
    candidate_count: int
    selected_centroid: tuple[float, float] | None
    estimate: ProgressEstimate
    boundary_anchor_source: BoundaryAnchorSource | None = None


@dataclass(frozen=True)
class ProgressSessionResult:
    """Frame-aligned generic progress output and optional calibration evidence."""

    frames: tuple[ProgressFrameResult, ...]
    calibration: LapLengthCalibration | None


@dataclass(frozen=True)
class _RawSessionFrame:
    frame: int
    time_s: float
    speed_kmh: float | None
    speed_quality: QualityFlag
    lap_state: LapState
    candidates: tuple[RedDotCandidate, ...]


def wrapped_delta(value: float, reference: float) -> float:
    """Return value-reference on the normalized interval (-0.5, 0.5]."""
    delta = (value - reference) % 1.0
    return delta - 1.0 if delta > 0.5 else delta


def _wrapped01(value: float) -> float:
    return value % 1.0


def _distance_fraction(
    first: AnchorFrameEvidence,
    second: AnchorFrameEvidence,
    lap_length: float,
) -> float:
    return abs(second.distance_m - first.distance_m) / lap_length


def _inside_gap(
    frame: AnchorFrameEvidence,
    boundary: AnchorFrameEvidence,
    *,
    max_gap_s: float,
    max_distance_fraction: float,
    lap_length: float,
) -> bool:
    return (
        abs(frame.time_s - boundary.time_s) <= max_gap_s
        and _distance_fraction(frame, boundary, lap_length)
        <= max_distance_fraction
    )


def _missing_boundary_anchor(unavailable_uncertainty: float) -> BoundaryVisualAnchor:
    return BoundaryVisualAnchor(
        raw_s=None,
        centroid=None,
        uncertainty=unavailable_uncertainty,
        source=BoundaryAnchorSource.MISSING,
    )


def _unique_projection(
    projections: tuple[VisualProjection, ...],
    *,
    last_raw_s: float | None,
    max_centerline_distance_px: float,
    min_score_margin: float,
) -> VisualProjection | None:
    scored = []
    for projection in projections:
        if projection.distance_px > max_centerline_distance_px:
            continue
        continuity = (
            0.0
            if last_raw_s is None
            else abs(wrapped_delta(projection.s_visual, last_raw_s)) / 0.5
        )
        score = projection.distance_px / max_centerline_distance_px + continuity
        scored.append((score, projection))
    scored.sort(
        key=lambda item: (
            item[0],
            item[1].s_visual,
            item[1].centroid[1],
            item[1].centroid[0],
        )
    )
    if not scored:
        return None
    if len(scored) > 1:
        score_gap = scored[1][0] - scored[0][0]
        if isclose(scored[1][0], scored[0][0]) or score_gap < min_score_margin:
            return None
    return scored[0][1]


def _nearest_projection_frame(
    frames: tuple[AnchorFrameEvidence, ...],
    boundary_index: int,
    step: int,
    *,
    max_centerline_distance_px: float,
    max_gap_s: float,
    max_distance_fraction: float,
    lap_length: float,
) -> AnchorFrameEvidence | None:
    boundary = frames[boundary_index]
    index = boundary_index + step
    while 0 <= index < len(frames):
        frame = frames[index]
        if frame.boundary is not None:
            return None
        if not _inside_gap(
            frame,
            boundary,
            max_gap_s=max_gap_s,
            max_distance_fraction=max_distance_fraction,
            lap_length=lap_length,
        ):
            return None
        if any(
            projection.distance_px <= max_centerline_distance_px
            for projection in frame.projections
        ):
            return frame
        index += step
    return None


def recover_boundary_visual_anchor(
    frames: tuple[AnchorFrameEvidence, ...],
    *,
    boundary_index: int,
    effective_lap_length_m: float,
    last_raw_s: float | None,
    max_centerline_distance_px: float,
    max_progress_error: float,
    min_score_margin: float,
    unavailable_uncertainty: float,
    settings: BoundaryAnchorSettings,
) -> BoundaryVisualAnchor:
    """Recover visual evidence for an already confirmed lap boundary."""
    missing = _missing_boundary_anchor(unavailable_uncertainty)
    if (
        not 0 <= boundary_index < len(frames)
        or effective_lap_length_m <= 0
        or max_centerline_distance_px <= 0
    ):
        return missing

    boundary = frames[boundary_index]
    if boundary.boundary is None:
        return missing
    exact = _unique_projection(
        boundary.projections,
        last_raw_s=last_raw_s,
        max_centerline_distance_px=max_centerline_distance_px,
        min_score_margin=min_score_margin,
    )
    if exact is not None:
        return BoundaryVisualAnchor(
            raw_s=exact.s_visual,
            centroid=exact.centroid,
            uncertainty=0.0,
            source=BoundaryAnchorSource.EXACT,
        )
    if any(
        projection.distance_px <= max_centerline_distance_px
        for projection in boundary.projections
    ):
        return missing

    before = _nearest_projection_frame(
        frames,
        boundary_index,
        -1,
        max_centerline_distance_px=max_centerline_distance_px,
        max_gap_s=settings.max_bracketing_gap_s,
        max_distance_fraction=settings.max_bracketing_distance_fraction,
        lap_length=effective_lap_length_m,
    )
    after = _nearest_projection_frame(
        frames,
        boundary_index,
        1,
        max_centerline_distance_px=max_centerline_distance_px,
        max_gap_s=settings.max_bracketing_gap_s,
        max_distance_fraction=settings.max_bracketing_distance_fraction,
        lap_length=effective_lap_length_m,
    )
    bracketing_frames = (before, after)
    if before is not None and after is not None and all(
        _inside_gap(
            frame,
            boundary,
            max_gap_s=settings.max_bracketing_gap_s,
            max_distance_fraction=settings.max_bracketing_distance_fraction,
            lap_length=effective_lap_length_m,
        )
        for frame in bracketing_frames
    ):
        pairs: list[tuple[float, VisualProjection, VisualProjection]] = []
        normalized_distance = _distance_fraction(
            before,
            after,
            effective_lap_length_m,
        )
        for before_projection in before.projections:
            if before_projection.distance_px > max_centerline_distance_px:
                continue
            for after_projection in after.projections:
                if after_projection.distance_px > max_centerline_distance_px:
                    continue
                pair_error = abs(
                    abs(
                        wrapped_delta(
                            after_projection.s_visual,
                            before_projection.s_visual,
                        )
                    )
                    - normalized_distance
                )
                if pair_error > max_progress_error:
                    continue
                score = (
                    pair_error
                    + before_projection.distance_px / max_centerline_distance_px
                    + after_projection.distance_px / max_centerline_distance_px
                )
                pairs.append((score, before_projection, after_projection))
        pairs.sort(
            key=lambda item: (
                item[0],
                item[1].s_visual,
                item[2].s_visual,
                item[1].centroid,
                item[2].centroid,
            )
        )
        has_unique_best_pair = bool(pairs) and (
            len(pairs) == 1
            or (
                not isclose(pairs[1][0], pairs[0][0])
                and pairs[1][0] - pairs[0][0] >= min_score_margin
            )
        )
        if has_unique_best_pair:
            _, before_projection, after_projection = pairs[0]
            total_distance = abs(after.distance_m - before.distance_m)
            if total_distance > 0:
                ratio = abs(boundary.distance_m - before.distance_m) / total_distance
            else:
                total_time = abs(after.time_s - before.time_s)
                ratio = (
                    0.5
                    if total_time == 0
                    else abs(boundary.time_s - before.time_s) / total_time
                )
            raw_s = _wrapped01(
                before_projection.s_visual
                + wrapped_delta(
                    after_projection.s_visual,
                    before_projection.s_visual,
                )
                * ratio
            )
            centroid = (
                before_projection.centroid[0]
                + (after_projection.centroid[0] - before_projection.centroid[0])
                * ratio,
                before_projection.centroid[1]
                + (after_projection.centroid[1] - before_projection.centroid[1])
                * ratio,
            )
            consumed_gate = max(
                abs(frame.time_s - boundary.time_s)
                / settings.max_bracketing_gap_s
                for frame in bracketing_frames
            )
            consumed_gate = max(
                consumed_gate,
                *(
                    _distance_fraction(frame, boundary, effective_lap_length_m)
                    / settings.max_bracketing_distance_fraction
                    for frame in bracketing_frames
                ),
            )
            return BoundaryVisualAnchor(
                raw_s=raw_s,
                centroid=centroid,
                uncertainty=(
                    0.25 * unavailable_uncertainty * min(1.0, consumed_gate)
                ),
                source=BoundaryAnchorSource.INTERPOLATED,
            )
        return missing

    one_sided: list[tuple[AnchorFrameEvidence, VisualProjection]] = []
    for frame in bracketing_frames:
        if frame is None or not _inside_gap(
            frame,
            boundary,
            max_gap_s=settings.max_one_sided_gap_s,
            max_distance_fraction=settings.max_one_sided_distance_fraction,
            lap_length=effective_lap_length_m,
        ):
            continue
        projection = _unique_projection(
            frame.projections,
            last_raw_s=last_raw_s,
            max_centerline_distance_px=max_centerline_distance_px,
            min_score_margin=min_score_margin,
        )
        if projection is not None:
            one_sided.append((frame, projection))
    if len(one_sided) != 1:
        return missing

    frame, projection = one_sided[0]
    consumed_gate = max(
        abs(frame.time_s - boundary.time_s) / settings.max_one_sided_gap_s,
        _distance_fraction(frame, boundary, effective_lap_length_m)
        / settings.max_one_sided_distance_fraction,
    )
    return BoundaryVisualAnchor(
        raw_s=projection.s_visual,
        centroid=projection.centroid,
        uncertainty=0.50 * unavailable_uncertainty * min(1.0, consumed_gate),
        source=BoundaryAnchorSource.NEAREST,
    )


def infer_centerline_direction(
    projections: tuple[VisualProjection, ...],
    *,
    anchor_s: float,
    predicted_s: float,
    min_error_margin: float,
) -> int | None:
    """Choose centerline order only when one orientation clearly fits odometry."""
    hypotheses = sorted(
        (
            (
                abs(
                    wrapped_delta(
                        ((projection.s_visual - anchor_s) * direction) % 1.0,
                        predicted_s,
                    )
                ),
                direction,
            )
            for projection in projections
            for direction in (1, -1)
        ),
        key=lambda item: (item[0], -item[1]),
    )
    if not hypotheses:
        return None
    best_error, best_direction = hypotheses[0]
    competing_errors = [
        error for error, direction in hypotheses if direction != best_direction
    ]
    if not competing_errors or min(competing_errors) - best_error < min_error_margin:
        return None
    return best_direction


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


class FusedProgressEstimator:
    """Fuse odometric prediction and accepted vision after a trusted anchor."""

    def __init__(
        self,
        *,
        effective_lap_length_m: float | None,
        visual_gain: float,
        short_visual_gap_s: float,
        unavailable_uncertainty: float,
    ):
        self.effective_lap_length_m = effective_lap_length_m
        self.visual_gain = visual_gain
        self.short_visual_gap_s = short_visual_gap_s
        self.unavailable_uncertainty = unavailable_uncertainty
        self._anchored = False
        self._lap_start_distance_m = 0.0
        self._last_s = 0.0
        self._last_time_s: float | None = None
        self._last_visual_time_s: float | None = None
        self._uncertainty = 0.0
        self._lap_start_odometry_uncertainty = 0.0

    def _unavailable(
        self,
        odometry: OdometryPoint,
        reasons: tuple[str, ...],
        *,
        anchored: bool,
    ) -> ProgressEstimate:
        return ProgressEstimate(
            s_fused=None,
            s_odometry=None,
            s_visual=None,
            distance_m=odometry.distance_m,
            effective_lap_length_m=self.effective_lap_length_m,
            uncertainty=min(1.0, self._uncertainty),
            source=ProgressSource.MISSING,
            reasons=reasons,
            anchored=anchored,
        )

    def update(
        self,
        odometry: OdometryPoint,
        visual: VisualSelection,
        boundary: ConfirmedLapBoundary | None,
        *,
        boundary_anchor: BoundaryVisualAnchor | None = None,
    ) -> ProgressEstimate:
        """Advance one frame without allowing implicit lap wraparound."""
        if boundary is not None:
            anchor_reason = (
                BoundaryAnchorSource.MISSING.value
                if boundary_anchor is None
                else boundary_anchor.source.value
            )
            anchor_uncertainty = (
                self.unavailable_uncertainty
                if boundary_anchor is None
                else boundary_anchor.uncertainty
            )
            boundary_source = {
                BoundaryAnchorSource.EXACT: ProgressSource.OBSERVED,
                BoundaryAnchorSource.INTERPOLATED: ProgressSource.INTERPOLATED,
                BoundaryAnchorSource.NEAREST: ProgressSource.PREDICTED,
                BoundaryAnchorSource.MISSING: ProgressSource.OBSERVED,
            }[
                BoundaryAnchorSource.MISSING
                if boundary_anchor is None
                else boundary_anchor.source
            ]
            self._anchored = True
            self._lap_start_distance_m = odometry.distance_m
            self._last_s = 0.0
            self._last_time_s = odometry.time_s
            self._last_visual_time_s = odometry.time_s
            self._lap_start_odometry_uncertainty = odometry.uncertainty
            self._uncertainty = anchor_uncertainty
            if self.effective_lap_length_m is None:
                return self._unavailable(
                    odometry,
                    (
                        "lap_boundary_confirmed",
                        anchor_reason,
                        "calibration_unavailable",
                    ),
                    anchored=True,
                )
            return ProgressEstimate(
                s_fused=0.0,
                s_odometry=0.0,
                s_visual=None,
                distance_m=odometry.distance_m,
                effective_lap_length_m=self.effective_lap_length_m,
                uncertainty=self._uncertainty,
                source=boundary_source,
                reasons=("lap_boundary_confirmed", anchor_reason),
                anchored=True,
            )

        if not self._anchored:
            self._last_time_s = odometry.time_s
            self._uncertainty = max(self._uncertainty, odometry.uncertainty)
            return self._unavailable(odometry, ("unanchored",), anchored=False)
        if self.effective_lap_length_m is None:
            self._last_time_s = odometry.time_s
            self._uncertainty = max(self._uncertainty, odometry.uncertainty)
            return self._unavailable(
                odometry,
                ("calibration_unavailable",),
                anchored=True,
            )

        delta_distance_m = odometry.delta_distance_m or 0.0
        predicted = min(
            1.0,
            max(
                0.0,
                self._last_s + delta_distance_m / self.effective_lap_length_m,
            ),
        )
        lap_distance_m = max(0.0, odometry.distance_m - self._lap_start_distance_m)
        s_odometry = min(1.0, lap_distance_m / self.effective_lap_length_m)
        elapsed = (
            0.0
            if self._last_time_s is None
            else max(0.0, odometry.time_s - self._last_time_s)
        )
        lap_odometry_uncertainty = max(
            0.0,
            odometry.uncertainty - self._lap_start_odometry_uncertainty,
        )
        base_uncertainty = max(self._uncertainty, lap_odometry_uncertainty)

        if visual.s_visual is not None:
            correction = wrapped_delta(visual.s_visual, predicted)
            fused = min(
                1.0,
                max(0.0, predicted + self.visual_gain * correction),
            )
            uncertainty = (
                (1.0 - self.visual_gain) * base_uncertainty
                + self.visual_gain * visual.uncertainty
            )
            source = ProgressSource.FUSED
            reasons = ("visual_correction",)
            self._last_visual_time_s = odometry.time_s
        else:
            visual_gap_s = (
                0.0
                if self._last_visual_time_s is None
                else odometry.time_s - self._last_visual_time_s
            )
            uncertainty = min(
                1.0,
                base_uncertainty
                + elapsed
                * self.unavailable_uncertainty
                / self.short_visual_gap_s,
            )
            reasons = visual.reasons
            if odometry.source is ProgressSource.INTERPOLATED:
                source = ProgressSource.INTERPOLATED
                reasons = tuple(dict.fromkeys((*reasons, "speed_gap_interpolated")))
            elif odometry.source is ProgressSource.MISSING:
                source = ProgressSource.MISSING
                uncertainty = max(uncertainty, self.unavailable_uncertainty)
            else:
                source = ProgressSource.PREDICTED
            fused = predicted
            if visual_gap_s > self.short_visual_gap_s:
                uncertainty = max(uncertainty, self.unavailable_uncertainty)

        self._last_s = fused
        self._last_time_s = odometry.time_s
        self._uncertainty = min(1.0, uncertainty)
        if self._uncertainty >= self.unavailable_uncertainty:
            return ProgressEstimate(
                s_fused=None,
                s_odometry=s_odometry,
                s_visual=visual.s_visual,
                distance_m=odometry.distance_m,
                effective_lap_length_m=self.effective_lap_length_m,
                uncertainty=self._uncertainty,
                source=ProgressSource.MISSING,
                reasons=tuple(dict.fromkeys((*reasons, "uncertainty_limit"))),
                anchored=True,
            )
        return ProgressEstimate(
            s_fused=fused,
            s_odometry=s_odometry,
            s_visual=visual.s_visual,
            distance_m=odometry.distance_m,
            effective_lap_length_m=self.effective_lap_length_m,
            uncertainty=self._uncertainty,
            source=source,
            reasons=reasons,
            anchored=True,
        )


def estimate_progress(
    observations: list[ProgressReplayObservation],
    *,
    max_missing_speed_fraction: float,
    max_relative_mad: float,
    visual_gain: float,
    short_visual_gap_s: float,
    unavailable_uncertainty: float,
) -> ProgressReplayResult:
    """Calibrate complete laps, then replay every observation through fusion."""
    trace = [observation.odometry for observation in observations]
    boundaries = [
        observation.boundary
        for observation in observations
        if observation.boundary is not None
    ]
    calibration = calibrate_effective_lap_length(
        summarize_lap_distances(trace, boundaries),
        max_missing_speed_fraction=max_missing_speed_fraction,
        max_relative_mad=max_relative_mad,
    )
    estimator = FusedProgressEstimator(
        effective_lap_length_m=calibration.effective_lap_length_m,
        visual_gain=visual_gain,
        short_visual_gap_s=short_visual_gap_s,
        unavailable_uncertainty=unavailable_uncertainty,
    )
    estimates = tuple(
        estimator.update(
            observation.odometry,
            observation.visual,
            observation.boundary,
        )
        for observation in observations
    )
    return ProgressReplayResult(estimates, calibration)


class ProgressSessionEstimator:
    """Collect raw frame evidence, then calibrate and fuse it offline."""

    def __init__(
        self,
        *,
        settings: ProgressSettings,
        lap_confirmer: LapTransitionConfirmer,
        white_lower: tuple[int, int, int],
        white_upper: tuple[int, int, int],
        centerline: Centerline | None = None,
    ):
        self.settings = settings
        self.lap_confirmer = lap_confirmer
        self.white_lower = white_lower
        self.white_upper = white_upper
        self.centerline = centerline
        self.map_error_reason: str | None = None
        self._roi_diagonal_px: float | None = None
        self._frames: list[_RawSessionFrame] = []

    def prepare_map(
        self,
        map_rois: list[np.ndarray],
        *,
        frequency_threshold: float | None,
    ) -> bool:
        """Build one centerline and retain explicit topology failure evidence."""
        if frequency_threshold is None:
            raise ValueError("frequency_threshold is required for generic progress")
        try:
            probability = build_white_probability(
                map_rois,
                white_lower=self.white_lower,
                white_upper=self.white_upper,
            )
            centerline_settings = self.settings.centerline
            self.centerline = build_centerline(
                probability,
                frequency_threshold=frequency_threshold,
                max_branch_length_fraction=(
                    centerline_settings.max_branch_length_fraction
                ),
                min_cycle_diagonal_fraction=(
                    centerline_settings.min_cycle_diagonal_fraction
                ),
                resample_spacing_diagonal_fraction=(
                    centerline_settings.resample_spacing_diagonal_fraction
                ),
            )
            self._roi_diagonal_px = hypot(*probability.shape)
        except (CenterlineTopologyError, ValueError) as error:
            self.centerline = None
            self.map_error_reason = getattr(error, "reason", str(error))
            return False
        self.map_error_reason = None
        return True

    def observe_frame(
        self,
        *,
        frame: int,
        time_s: float,
        speed_kmh: float | None,
        raw_lap_number: int | None,
        map_roi: np.ndarray | None,
        speed_quality: QualityFlag | None = None,
    ) -> None:
        """Retain one frame's raw evidence without producing fused truth."""
        lap_state = self.lap_confirmer.observe(
            LapObservation(frame, time_s, raw_lap_number)
        )
        candidate_settings = self.settings.candidates
        candidates = extract_red_candidates(
            map_roi,
            min_area_fraction=candidate_settings.min_area_fraction,
            max_area_fraction=candidate_settings.max_area_fraction,
            min_circularity=candidate_settings.min_circularity,
            min_compact_aspect_ratio=(
                candidate_settings.min_compact_aspect_ratio
            ),
            min_filled_extent=candidate_settings.min_filled_extent,
            min_convex_compactness=(
                candidate_settings.min_convex_compactness
            ),
        )
        if map_roi is not None and map_roi.size > 0 and self._roi_diagonal_px is None:
            self._roi_diagonal_px = hypot(*map_roi.shape[:2])
        quality = speed_quality or (
            QualityFlag.OBSERVED if speed_kmh is not None else QualityFlag.MISSING
        )
        self._frames.append(
            _RawSessionFrame(
                frame,
                time_s,
                speed_kmh,
                quality,
                lap_state,
                candidates,
            )
        )

    @staticmethod
    def _missing_visual(reason: str = "visual_missing") -> VisualSelection:
        return VisualSelection(
            None,
            None,
            None,
            0.0,
            ProgressSource.MISSING,
            (reason,),
        )

    def _projections(
        self,
        candidates: tuple[RedDotCandidate, ...],
    ) -> tuple[VisualProjection, ...]:
        if self.centerline is None or self._roi_diagonal_px is None:
            return ()
        maximum = self._max_centerline_distance_px()
        return tuple(
            projection
            for candidate in candidates
            for projection in project_candidate(
                candidate,
                self.centerline,
                max_distance_px=maximum,
            )
        )

    def _max_centerline_distance_px(self) -> float:
        return (
            (self._roi_diagonal_px or 1.0)
            * self.settings.projection.max_centerline_distance_diagonal_fraction
        )

    def finalize(self) -> ProgressSessionResult:
        """Integrate, calibrate, associate vision, and return frame-aligned truth."""
        if not self._frames:
            return ProgressSessionResult((), None)
        speed_observations = [
            SpeedObservation(
                frame.time_s,
                frame.speed_kmh,
                frame.speed_quality,
            )
            for frame in self._frames
        ]
        odometry_settings = self.settings.odometry
        odometry = integrate_speed(
            speed_observations,
            max_interpolation_gap_s=odometry_settings.max_interpolation_gap_s,
            observed_uncertainty_per_s=odometry_settings.observed_uncertainty_per_s,
            interpolated_uncertainty_per_s=(
                odometry_settings.interpolated_uncertainty_per_s
            ),
        )
        boundaries = [
            frame.lap_state.boundary
            for frame in self._frames
            if frame.lap_state.boundary is not None
        ]
        calibration_settings = self.settings.calibration
        calibration = calibrate_effective_lap_length(
            summarize_lap_distances(odometry, boundaries),
            max_missing_speed_fraction=(
                calibration_settings.max_missing_speed_fraction
            ),
            max_relative_mad=calibration_settings.max_relative_mad,
        )
        estimator = FusedProgressEstimator(
            effective_lap_length_m=calibration.effective_lap_length_m,
            visual_gain=self.settings.fusion.visual_gain,
            short_visual_gap_s=self.settings.fusion.short_visual_gap_s,
            unavailable_uncertainty=self.settings.fusion.unavailable_uncertainty,
        )
        projection_frames = tuple(
            AnchorFrameEvidence(
                time_s=frame.time_s,
                distance_m=point.distance_m,
                projections=self._projections(frame.candidates),
                boundary=frame.lap_state.boundary,
            )
            for frame, point in zip(self._frames, odometry)
        )
        maximum_centerline_distance_px = self._max_centerline_distance_px()

        raw_anchor_s: float | None = None
        direction: int | None = None
        last_raw_s: float | None = None
        last_centroid: tuple[float, float] | None = None
        previous_displacement_px: float | None = None
        lap_start_distance_m = 0.0
        lap_start_odometry_uncertainty = 0.0
        results: list[ProgressFrameResult] = []

        for frame_index, (frame, point) in enumerate(zip(self._frames, odometry)):
            projections = projection_frames[frame_index].projections
            boundary = frame.lap_state.boundary
            boundary_anchor: BoundaryVisualAnchor | None = None
            boundary_anchor_source: BoundaryAnchorSource | None = None
            selected = self._missing_visual(
                self.map_error_reason or "visual_missing"
            )
            effective_length = calibration.effective_lap_length_m
            predicted_s = (
                0.0
                if effective_length is None
                else min(
                    1.0,
                    max(
                        0.0,
                        (point.distance_m - lap_start_distance_m)
                        / effective_length,
                    ),
                )
            )
            if boundary is not None:
                lap_start_distance_m = point.distance_m
                lap_start_odometry_uncertainty = point.uncertainty
                boundary_anchor = recover_boundary_visual_anchor(
                    projection_frames,
                    boundary_index=frame_index,
                    effective_lap_length_m=effective_length or 0.0,
                    last_raw_s=last_raw_s,
                    max_centerline_distance_px=maximum_centerline_distance_px,
                    max_progress_error=self.settings.projection.max_progress_error,
                    min_score_margin=self.settings.projection.min_score_margin,
                    unavailable_uncertainty=(
                        self.settings.fusion.unavailable_uncertainty
                    ),
                    settings=self.settings.boundary_anchor,
                )
                boundary_anchor_source = boundary_anchor.source
                if boundary_anchor.source is BoundaryAnchorSource.MISSING:
                    raw_anchor_s = None
                    direction = None
                    last_raw_s = None
                    last_centroid = None
                    previous_displacement_px = None
                else:
                    raw_anchor_s = boundary_anchor.raw_s
                    last_raw_s = boundary_anchor.raw_s
                    last_centroid = boundary_anchor.centroid
                    previous_displacement_px = None
                    direction = None
            elif projections and raw_anchor_s is None:
                raw = min(
                    projections,
                    key=lambda projection: (
                        projection.distance_px,
                        projection.s_visual,
                    ),
                )
                last_raw_s = raw.s_visual
                last_centroid = raw.centroid
            elif projections and raw_anchor_s is not None:
                raw = min(
                    projections,
                    key=lambda projection: (
                        abs(
                            wrapped_delta(
                                projection.s_visual,
                                last_raw_s if last_raw_s is not None else raw_anchor_s,
                            )
                        ),
                        projection.distance_px,
                    ),
                )
                if direction is None:
                    direction = infer_centerline_direction(
                        projections,
                        anchor_s=raw_anchor_s,
                        predicted_s=predicted_s,
                        min_error_margin=(
                            self.settings.projection.min_score_margin
                            * self.settings.projection.max_progress_error
                        ),
                    )
                last_raw_s = raw.s_visual
                if direction is not None:
                    normalized_projections = tuple(
                        VisualProjection(
                            s_visual=(
                                (projection.s_visual - raw_anchor_s) * direction
                            )
                            % 1.0,
                            distance_px=projection.distance_px,
                            projected_xy=projection.projected_xy,
                            centroid=projection.centroid,
                        )
                        for projection in projections
                    )
                    selected = select_visual_projection(
                        normalized_projections,
                        predicted_s=predicted_s,
                        current_uncertainty=max(
                            0.0,
                            point.uncertainty - lap_start_odometry_uncertainty,
                        ),
                        last_centroid=last_centroid,
                        previous_displacement_px=previous_displacement_px,
                        speed_kmh=frame.speed_kmh,
                        delta_time_s=(
                            0.0
                            if not results
                            else frame.time_s - self._frames[len(results) - 1].time_s
                        ),
                        roi_diagonal_px=self._roi_diagonal_px or 1.0,
                        max_centerline_distance_diagonal_fraction=(
                            self.settings.projection.max_centerline_distance_diagonal_fraction
                        ),
                        max_progress_error=self.settings.projection.max_progress_error,
                        min_score_margin=self.settings.projection.min_score_margin,
                    )
                    if selected.centroid is not None:
                        if last_centroid is not None:
                            previous_displacement_px = hypot(
                                selected.centroid[0] - last_centroid[0],
                                selected.centroid[1] - last_centroid[1],
                            )
                        last_centroid = selected.centroid

            estimate = estimator.update(
                point,
                selected,
                boundary,
                boundary_anchor=boundary_anchor,
            )
            results.append(
                ProgressFrameResult(
                    frame=frame.frame,
                    raw_lap_number=frame.lap_state.raw_lap_number,
                    confirmed_lap_number=frame.lap_state.confirmed_lap_number,
                    boundary=boundary,
                    boundary_confidence=frame.lap_state.confidence,
                    candidate_count=len(frame.candidates),
                    selected_centroid=selected.centroid,
                    estimate=estimate,
                    boundary_anchor_source=boundary_anchor_source,
                )
            )
        return ProgressSessionResult(tuple(results), calibration)
