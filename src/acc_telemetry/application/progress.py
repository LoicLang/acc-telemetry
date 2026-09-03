"""Pure temporal selection and fusion for generic longitudinal progress."""

from __future__ import annotations

from dataclasses import dataclass
from math import hypot

from acc_telemetry.application.odometry import (
    LapLengthCalibration,
    OdometryPoint,
    calibrate_effective_lap_length,
    summarize_lap_distances,
)
from acc_telemetry.domain.progress import (
    ConfirmedLapBoundary,
    ProgressEstimate,
    ProgressSource,
)
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
    ) -> ProgressEstimate:
        """Advance one frame without allowing implicit lap wraparound."""
        if boundary is not None:
            self._anchored = True
            self._lap_start_distance_m = odometry.distance_m
            self._last_s = 0.0
            self._last_time_s = odometry.time_s
            self._last_visual_time_s = odometry.time_s
            self._uncertainty = min(1.0, odometry.uncertainty)
            if self.effective_lap_length_m is None:
                return self._unavailable(
                    odometry,
                    ("lap_boundary_confirmed", "calibration_unavailable"),
                    anchored=True,
                )
            return ProgressEstimate(
                s_fused=0.0,
                s_odometry=0.0,
                s_visual=None,
                distance_m=odometry.distance_m,
                effective_lap_length_m=self.effective_lap_length_m,
                uncertainty=self._uncertainty,
                source=ProgressSource.OBSERVED,
                reasons=("lap_boundary_confirmed",),
                anchored=True,
            )

        if not self._anchored or self.effective_lap_length_m is None:
            self._last_time_s = odometry.time_s
            self._uncertainty = max(self._uncertainty, odometry.uncertainty)
            return self._unavailable(odometry, ("unanchored",), anchored=False)

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
        base_uncertainty = max(self._uncertainty, odometry.uncertainty)

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
