#!/usr/bin/env python3
"""Generate ignored evidence for generic longitudinal progress validation."""

from __future__ import annotations

import argparse
import bisect
import csv
import json
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from acc_telemetry.application.components import build_components
from acc_telemetry.application.config import load_settings
from acc_telemetry.application.pipeline import TelemetryPipeline


TRACE_FIELDS = (
    "frame",
    "time",
    "raw_lap_number",
    "confirmed_lap_number",
    "boundary_confidence",
    "boundary_confirmed",
    "boundary_anchor_source",
    "candidate_count",
    "selected_x",
    "selected_y",
    "track_position",
    "s_odometry",
    "s_visual",
    "s_fused",
    "distance_m",
    "effective_lap_length_m",
    "uncertainty",
    "source",
    "reasons",
    "anchored",
)


def write_trace(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    """Write frame evidence using the stable generic progress schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=TRACE_FIELDS,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def _optional_float(value: Any) -> float | None:
    if value is None or str(value).strip() == "":
        return None
    return float(value)


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes"}


def summarize_trace(rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Compute deterministic validation metrics from frame-aligned evidence."""
    materialized = list(rows)
    source_counts = Counter(
        str(row.get("source")) for row in materialized if row.get("source")
    )
    confirmed_boundary_count = sum(
        _truthy(row.get("boundary_confirmed")) for row in materialized
    )
    boundary_anchor_source_counts = Counter(
        str(row.get("boundary_anchor_source"))
        for row in materialized
        if _truthy(row.get("boundary_confirmed"))
        and row.get("boundary_anchor_source")
    )
    premature_completion_count = sum(
        not _truthy(row.get("boundary_confirmed"))
        and (value := _optional_float(row.get("s_fused"))) is not None
        and value >= 0.999
        and (
            (odometry := _optional_float(row.get("s_odometry"))) is None
            or odometry < 0.99
        )
        for row in materialized
    )
    unconfirmed_reset_count = 0
    nonlocal_visual_jump_count = 0
    previous_s: float | None = None
    for row in materialized:
        current_s = _optional_float(row.get("s_fused"))
        if current_s is None:
            previous_s = None
            continue
        if previous_s is not None and not _truthy(row.get("boundary_confirmed")):
            if previous_s >= 0.9 and current_s <= 0.1:
                unconfirmed_reset_count += 1
            wrapped = abs(((current_s - previous_s + 0.5) % 1.0) - 0.5)
            if wrapped > 0.1:
                nonlocal_visual_jump_count += 1
        previous_s = current_s

    lap_points: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for row in materialized:
        lap = row.get("confirmed_lap_number")
        s_odometry = _optional_float(row.get("s_odometry"))
        s_fused = _optional_float(row.get("s_fused"))
        if lap is None or s_odometry is None or s_fused is None:
            continue
        lap_points[int(lap)].append((s_odometry, s_fused))
    curves: list[tuple[list[float], list[float]]] = []
    for points in lap_points.values():
        grouped: dict[float, list[float]] = defaultdict(list)
        for s_odometry, s_fused in points:
            grouped[s_odometry].append(s_fused)
        ordered = sorted(
            (position, sum(values) / len(values))
            for position, values in grouped.items()
        )
        if not ordered or ordered[0][0] > 0.01 or ordered[-1][0] < 0.99:
            continue
        curves.append(
            (
                [position for position, _ in ordered],
                [value for _, value in ordered],
            )
        )
    spreads = []
    for checkpoint in range(1, 100):
        target = checkpoint / 100.0
        values = []
        for positions, fused_values in curves:
            index = bisect.bisect_left(positions, target)
            if index < len(positions) and positions[index] == target:
                values.append(fused_values[index])
                continue
            if index == 0 or index == len(positions):
                continue
            lower_position = positions[index - 1]
            upper_position = positions[index]
            fraction = (target - lower_position) / (upper_position - lower_position)
            values.append(
                fused_values[index - 1]
                + fraction * (fused_values[index] - fused_values[index - 1])
            )
        if len(values) >= 2:
            spreads.append(max(values) - min(values))

    unavailable_duration = 0.0
    for previous, current in zip(materialized, materialized[1:]):
        if _optional_float(previous.get("s_fused")) is None:
            previous_time = _optional_float(previous.get("time"))
            current_time = _optional_float(current.get("time"))
            if previous_time is not None and current_time is not None:
                unavailable_duration += max(0.0, current_time - previous_time)

    return {
        "metric_scope": "internal_consistency_only",
        "spatial_accuracy": "not_evaluated",
        "frame_count": len(materialized),
        "confirmed_boundary_count": confirmed_boundary_count,
        "premature_completion_count": premature_completion_count,
        "unconfirmed_reset_count": unconfirmed_reset_count,
        "nonlocal_visual_jump_count": nonlocal_visual_jump_count,
        "max_checkpoint_spread": max(spreads) if spreads else None,
        "comparable_checkpoint_count": len(spreads),
        "source_counts": dict(source_counts),
        "boundary_anchor_source_counts": dict(boundary_anchor_source_counts),
        "unavailable_duration_s": unavailable_duration,
    }


def validate_output_paths(video_path: Path, output_dir: Path) -> None:
    """Refuse any diagnostic destination that could overwrite the input video."""
    video = video_path.resolve()
    output = output_dir.resolve()
    if output == video or output / "trace.csv" == video or output / "summary.json" == video:
        raise ValueError("diagnostic output cannot be the input video")


def run_diagnostic(
    video_path: Path,
    profile_name: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Run the shared generic pipeline and write ignored validation evidence."""
    validate_output_paths(video_path, output_dir)
    settings = load_settings()
    profile = settings.profile(profile_name)
    components = build_components(
        str(video_path),
        profile_name,
        settings=settings,
        enable_performance_stats=True,
    )
    rows: list[dict[str, Any]] = []
    pipeline = TelemetryPipeline(
        video=components.video,
        controls=components.controls,
        laps=components.laps,
        progress=components.progress,
        has_track_map="track_map" in profile.rois,
        sample_count=components.sample_count,
        frequency_threshold=components.frequency_threshold,
        progress_callback=lambda percent, message: print(f"[{percent:3d}%] {message}"),
        position_diagnostic_callback=rows.append,
    )
    try:
        result = pipeline.run()
    finally:
        components.laps.close()

    output_dir.mkdir(parents=True, exist_ok=True)
    write_trace(output_dir / "trace.csv", rows)
    summary = summarize_trace(rows)
    calibration = result.progress_calibration
    summary.update({
        "input_path": str(video_path.resolve()),
        "input_size_bytes": video_path.stat().st_size,
        "profile": profile_name,
        "video_frame_count": result.video_info["frame_count"],
        "calibration_lap_count": (
            0 if calibration is None else len(calibration.accepted_laps)
        ),
        "rejected_calibration_laps": (
            []
            if calibration is None
            else [
                {"lap_number": lap.lap_number, "reasons": list(lap.reasons)}
                for lap in calibration.rejected_laps
            ]
        ),
        "effective_lap_length_m": (
            None if calibration is None else calibration.effective_lap_length_m
        ),
    })
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return summary


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate generic ACC minimap progress on an immutable capture."
    )
    parser.add_argument("video", type=Path)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args(argv)
    if not args.video.is_file():
        parser.error(f"video not found: {args.video}")
    try:
        summary = run_diagnostic(args.video, args.profile, args.output_dir)
    except ValueError as error:
        parser.error(str(error))
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
