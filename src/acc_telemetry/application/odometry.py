"""Pure speed integration and robust effective-lap-length calibration."""

from __future__ import annotations

from dataclasses import dataclass, replace
from statistics import median

from acc_telemetry.domain.progress import ConfirmedLapBoundary, ProgressSource
from acc_telemetry.domain.telemetry import QualityFlag


@dataclass(frozen=True)
class SpeedObservation:
    """One speed sample and its extraction quality."""

    time_s: float
    speed_kmh: float | None
    quality: QualityFlag


@dataclass(frozen=True)
class OdometryPoint:
    """Cumulative distance evidence at one timestamp."""

    time_s: float
    distance_m: float
    delta_distance_m: float | None
    uncertainty: float
    source: ProgressSource
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class LapDistanceSummary:
    """Integrated distance between two confirmed lap boundaries."""

    lap_number: int
    start_time_s: float
    end_time_s: float
    distance_m: float
    missing_speed_fraction: float
    complete: bool
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class LapLengthCalibration:
    """Robust effective distance and the laps that did or did not support it."""

    effective_lap_length_m: float | None
    uncertainty: float
    relative_mad: float | None
    accepted_laps: tuple[LapDistanceSummary, ...]
    rejected_laps: tuple[LapDistanceSummary, ...]


def _observed_speed(sample: SpeedObservation) -> float | None:
    if (
        sample.quality is QualityFlag.OBSERVED
        and sample.speed_kmh is not None
        and sample.speed_kmh >= 0
    ):
        return float(sample.speed_kmh)
    return None


def _missing_reason(*samples: SpeedObservation) -> str:
    if any(
        sample.quality is QualityFlag.ANOMALOUS
        or (sample.speed_kmh is not None and sample.speed_kmh < 0)
        for sample in samples
    ):
        return "speed_anomalous"
    return "speed_missing"


def _interpolated_speeds(
    samples: list[SpeedObservation],
    max_interpolation_gap_s: float,
) -> tuple[list[float | None], set[int]]:
    speeds = [_observed_speed(sample) for sample in samples]
    interpolated: set[int] = set()
    index = 0
    while index < len(samples):
        if speeds[index] is not None:
            index += 1
            continue
        start = index
        while index < len(samples) and speeds[index] is None:
            index += 1
        left = start - 1
        right = index
        if left < 0 or right >= len(samples):
            continue
        start_time = samples[left].time_s
        end_time = samples[right].time_s
        if end_time <= start_time or end_time - start_time > max_interpolation_gap_s:
            continue
        if any(
            samples[item].time_s <= samples[item - 1].time_s
            for item in range(left + 1, right + 1)
        ):
            continue
        start_speed = speeds[left]
        end_speed = speeds[right]
        if start_speed is None or end_speed is None:
            continue
        for item in range(start, right):
            fraction = (samples[item].time_s - start_time) / (end_time - start_time)
            speeds[item] = start_speed + fraction * (end_speed - start_speed)
            interpolated.add(item)
    return speeds, interpolated


def integrate_speed(
    samples: list[SpeedObservation],
    *,
    max_interpolation_gap_s: float,
    observed_uncertainty_per_s: float = 0.00005,
    interpolated_uncertainty_per_s: float = 0.001,
) -> list[OdometryPoint]:
    """Integrate speed with trapezoidal intervals and explicit gap provenance."""
    if not samples:
        return []

    speeds, interpolated = _interpolated_speeds(
        samples,
        max_interpolation_gap_s,
    )
    first_source = (
        ProgressSource.OBSERVED if speeds[0] is not None else ProgressSource.MISSING
    )
    first_reasons = () if speeds[0] is not None else (_missing_reason(samples[0]),)
    points = [
        OdometryPoint(
            time_s=samples[0].time_s,
            distance_m=0.0,
            delta_distance_m=None,
            uncertainty=0.0,
            source=first_source,
            reasons=first_reasons,
        )
    ]
    distance_m = 0.0
    uncertainty = 0.0

    for index in range(1, len(samples)):
        previous = samples[index - 1]
        current = samples[index]
        dt = current.time_s - previous.time_s
        reasons: tuple[str, ...]
        delta_distance_m: float | None = None

        if dt <= 0:
            source = ProgressSource.MISSING
            reasons = ("non_monotonic_time",)
        elif speeds[index - 1] is None or speeds[index] is None:
            source = ProgressSource.MISSING
            reasons = (_missing_reason(previous, current),)
            uncertainty = min(
                1.0,
                uncertainty + interpolated_uncertainty_per_s * dt,
            )
        else:
            delta_distance_m = (
                (speeds[index - 1] + speeds[index]) / 2.0 / 3.6 * dt
            )
            distance_m += delta_distance_m
            if index - 1 in interpolated or index in interpolated:
                source = ProgressSource.INTERPOLATED
                reasons = ("speed_gap_interpolated",)
                uncertainty = min(
                    1.0,
                    uncertainty + interpolated_uncertainty_per_s * dt,
                )
            else:
                source = ProgressSource.OBSERVED
                reasons = ()
                uncertainty = min(
                    1.0,
                    uncertainty + observed_uncertainty_per_s * dt,
                )

        points.append(
            OdometryPoint(
                time_s=current.time_s,
                distance_m=distance_m,
                delta_distance_m=delta_distance_m,
                uncertainty=uncertainty,
                source=source,
                reasons=reasons,
            )
        )

    return points


def _point_at_or_before(
    trace: list[OdometryPoint],
    time_s: float,
) -> OdometryPoint | None:
    matches = [point for point in trace if point.time_s <= time_s]
    return matches[-1] if matches else None


def summarize_lap_distances(
    trace: list[OdometryPoint],
    boundaries: list[ConfirmedLapBoundary],
) -> list[LapDistanceSummary]:
    """Summarize complete boundary-to-boundary odometric laps."""
    summaries: list[LapDistanceSummary] = []
    for start, end in zip(boundaries, boundaries[1:]):
        start_point = _point_at_or_before(trace, start.time_s)
        end_point = _point_at_or_before(trace, end.time_s)
        interval = [
            point for point in trace if start.time_s < point.time_s <= end.time_s
        ]
        complete = start_point is not None and end_point is not None
        distance = (
            end_point.distance_m - start_point.distance_m if complete else 0.0
        )
        missing_count = sum(
            point.source is ProgressSource.MISSING for point in interval
        )
        missing_fraction = missing_count / len(interval) if interval else 1.0
        reasons = () if complete else ("missing_boundary",)
        summaries.append(
            LapDistanceSummary(
                lap_number=start.to_lap,
                start_time_s=start.time_s,
                end_time_s=end.time_s,
                distance_m=distance,
                missing_speed_fraction=missing_fraction,
                complete=complete,
                reasons=reasons,
            )
        )
    return summaries


def _reject(
    summary: LapDistanceSummary,
    *extra_reasons: str,
) -> LapDistanceSummary:
    reasons = tuple(
        dict.fromkeys(
            (*summary.reasons, *extra_reasons, "calibration_lap_rejected")
        )
    )
    return replace(summary, reasons=reasons)


def calibrate_effective_lap_length(
    summaries: list[LapDistanceSummary],
    *,
    max_missing_speed_fraction: float,
    max_relative_mad: float,
) -> LapLengthCalibration:
    """Learn a robust median distance without allowing degraded laps to calibrate."""
    eligible: list[LapDistanceSummary] = []
    rejected: list[LapDistanceSummary] = []
    for summary in summaries:
        if summary.end_time_s <= summary.start_time_s:
            rejected.append(_reject(summary, "non_positive_duration"))
        elif (
            not summary.complete
            or summary.distance_m <= 0
            or summary.missing_speed_fraction > max_missing_speed_fraction
        ):
            rejected.append(_reject(summary))
        else:
            eligible.append(summary)

    accepted = eligible
    if len(eligible) >= 3:
        initial_median = median(summary.distance_m for summary in eligible)
        duration_median = median(
            summary.end_time_s - summary.start_time_s for summary in eligible
        )
        accepted = []
        for summary in eligible:
            relative_deviation = abs(summary.distance_m - initial_median) / initial_median
            duration = summary.end_time_s - summary.start_time_s
            duration_deviation = abs(duration - duration_median) / duration_median
            if relative_deviation > max_relative_mad:
                rejected.append(_reject(summary, "distance_outlier"))
            elif duration_deviation > max_relative_mad:
                rejected.append(_reject(summary, "duration_outlier"))
            else:
                accepted.append(summary)

    if not accepted:
        return LapLengthCalibration(None, 1.0, None, (), tuple(rejected))

    effective = float(median(summary.distance_m for summary in accepted))
    absolute_deviations = [
        abs(summary.distance_m - effective) for summary in accepted
    ]
    relative_mad = float(median(absolute_deviations) / effective)
    uncertainty = max_relative_mad if len(accepted) == 1 else relative_mad
    return LapLengthCalibration(
        effective_lap_length_m=effective,
        uncertainty=min(1.0, uncertainty),
        relative_mad=relative_mad,
        accepted_laps=tuple(accepted),
        rejected_laps=tuple(rejected),
    )
