"""Normalize legacy extractor rows without silently correcting evidence."""

import csv
import json
import math
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Protocol

from acc_telemetry.domain.progress import ProgressSource
from acc_telemetry.domain.telemetry import QualityFlag, TelemetrySample


class NormalizationLimits(Protocol):
    speed_min_kmh: float
    speed_max_kmh: float
    pedal_min_percent: float
    pedal_max_percent: float


def _optional_float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return float(value)


def _optional_int(value: Any) -> int | None:
    number = _optional_float(value)
    return None if number is None else int(number)


def _optional_bool(value: Any) -> bool | None:
    number = _optional_int(value)
    return None if number is None else bool(number)


def _lap_time_seconds(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    text = str(value).strip()
    if ":" not in text:
        return float(text)
    minutes, seconds = text.split(":", 1)
    return int(minutes) * 60 + float(seconds)


def _quality_hints(value: Any) -> dict[str, QualityFlag]:
    if value is None or str(value).strip() == "":
        return {}
    hints: dict[str, QualityFlag] = {}
    for item in str(value).split(";"):
        field, separator, flag = item.partition(":")
        if not separator:
            raise ValueError(f"Invalid quality hint: {item}")
        hints[field.strip()] = QualityFlag(flag.strip())
    return hints


def _reasons(value: Any) -> tuple[str, ...]:
    if value is None or str(value).strip() == "":
        return ()
    return tuple(reason.strip() for reason in str(value).split(";") if reason.strip())


def normalize_row(row: Mapping[str, Any], limits: NormalizationLimits) -> TelemetrySample:
    """Convert a legacy CSV row into the stable domain contract."""
    modern = any(key in row for key in ("s_fused", "s_source", "quality_hint"))
    if modern:
        for field in ("frame", "time", "lap_number", "raw_lap_number", "speed", "gear",
                      "throttle", "brake", "steering", "tc_active", "abs_active",
                      "track_position", "s_fused", "s_odometry", "s_visual", "s_uncertainty"):
            value = _optional_float(row.get(field))
            if value is not None and not math.isfinite(value):
                raise ValueError(f"non-finite modern field: {field}")
        lap_time = _lap_time_seconds(row.get("lap_time"))
        if lap_time is not None and not math.isfinite(lap_time):
            raise ValueError("non-finite modern field: lap_time")
    raw_reasons = row.get("field_reasons")
    field_reasons = {} if raw_reasons is None or raw_reasons == "" else (
        json.loads(raw_reasons) if isinstance(raw_reasons, str) else raw_reasons
    )
    if not isinstance(field_reasons, Mapping) or any(
        not isinstance(k, str) or not isinstance(v, (list, tuple))
        or any(not isinstance(reason, str) for reason in v)
        for k, v in field_reasons.items()
    ):
        raise ValueError("invalid field_reasons")
    source = dict(row)
    quality: dict[str, QualityFlag] = {}
    anomalies: list[str] = []

    track_position = _optional_float(row.get("track_position"))
    modern_progress = "s_fused" in row or "s_source" in row
    s_fused = _optional_float(row.get("s_fused"))
    s = (
        s_fused
        if modern_progress
        else (None if track_position is None else track_position / 100.0)
    )
    s_odometry = _optional_float(row.get("s_odometry"))
    s_visual = _optional_float(row.get("s_visual"))
    s_uncertainty = _optional_float(row.get("s_uncertainty"))
    source_text = row.get("s_source")
    s_source = (
        None
        if source_text is None or str(source_text).strip() == ""
        else ProgressSource(str(source_text).strip())
    )
    s_reasons = _reasons(row.get("s_reasons"))
    speed = _optional_float(row.get("speed"))
    throttle = _optional_float(row.get("throttle"))
    brake = _optional_float(row.get("brake"))
    steering = _optional_float(row.get("steering"))

    values = {
        "lap_number": _optional_int(row.get("lap_number")),
        "lap_time_s": _lap_time_seconds(row.get("lap_time")),
        "s": s,
        "speed_kmh": speed,
        "gear": _optional_int(row.get("gear")),
        "throttle_pct": throttle,
        "brake_pct": brake,
        "steering": steering,
        "tc_active": _optional_bool(row.get("tc_active")),
        "abs_active": _optional_bool(row.get("abs_active")),
    }
    for field, value in values.items():
        quality[field] = QualityFlag.MISSING if value is None else QualityFlag.OBSERVED

    quality.update(_quality_hints(row.get("quality_hint")))
    if s_source is not None:
        quality["s"] = QualityFlag(s_source.value)

    def mark_anomaly(field: str, reason: str) -> None:
        quality[field] = QualityFlag.ANOMALOUS
        anomalies.append(reason)

    if speed is not None and not limits.speed_min_kmh <= speed <= limits.speed_max_kmh:
        mark_anomaly(
            "speed_kmh",
            f"speed_kmh outside [{limits.speed_min_kmh:g}, {limits.speed_max_kmh:g}]",
        )
    if s is not None and not 0 <= s <= 1:
        mark_anomaly("s", "s outside [0, 1]")
    for field, value in (("throttle_pct", throttle), ("brake_pct", brake)):
        if value is not None and not limits.pedal_min_percent <= value <= limits.pedal_max_percent:
            mark_anomaly(
                field,
                f"{field} outside [{limits.pedal_min_percent:g}, {limits.pedal_max_percent:g}]",
            )
    if steering is not None and not -1 <= steering <= 1:
        mark_anomaly("steering", "steering outside [-1, 1]")

    return TelemetrySample(
        frame=int(row["frame"]),
        time_s=float(row["time"]),
        lap_number=values["lap_number"],
        lap_time_s=values["lap_time_s"],
        s=s,
        speed_kmh=speed,
        gear=values["gear"],
        throttle_pct=throttle,
        brake_pct=brake,
        steering=steering,
        tc_active=values["tc_active"],
        abs_active=values["abs_active"],
        field_quality=MappingProxyType(quality),
        field_reasons=MappingProxyType({k: tuple(v) for k, v in field_reasons.items()}),
        anomalies=tuple(anomalies),
        source_values=MappingProxyType(source),
        s_odometry=s_odometry,
        s_visual=s_visual,
        s_uncertainty=s_uncertainty,
        s_source=s_source,
        s_reasons=s_reasons,
    )


def load_csv_samples(path: Path | str, limits: NormalizationLimits) -> list[TelemetrySample]:
    """Load a legacy-compatible CSV as normalized samples."""
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return [normalize_row(row, limits) for row in csv.DictReader(handle)]
