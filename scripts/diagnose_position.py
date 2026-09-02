#!/usr/bin/env python3
"""Write an ignored diagnostic trace for ACC minimap position tracking."""

from __future__ import annotations

import argparse
import csv
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

from acc_telemetry.application.components import build_components
from acc_telemetry.application.config import load_settings
from acc_telemetry.application.pipeline import TelemetryPipeline


TRACE_FIELDS = (
    "frame",
    "time",
    "lap_number",
    "track_position",
    "dot_x",
    "dot_y",
    "closest_idx",
    "start_idx",
    "start_source",
    "travel_direction",
    "raw_position",
    "completion_forced",
    "validated_position",
    "decision",
)


def write_trace(path: Path, rows: Iterable[Mapping[str, Any]]) -> None:
    """Write diagnostic rows using the stable trace schema."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACE_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def run_diagnostic(video_path: Path, profile_name: str, output_path: Path) -> None:
    """Run the shared pipeline while streaming position evidence to CSV."""
    settings = load_settings()
    profile = settings.profile(profile_name)
    components = build_components(
        str(video_path),
        profile_name,
        settings=settings,
        enable_performance_stats=True,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TRACE_FIELDS)
        writer.writeheader()
        pipeline = TelemetryPipeline(
            video=components.video,
            controls=components.controls,
            laps=components.laps,
            position=components.position,
            has_track_map="track_map" in profile.rois,
            sample_count=components.sample_count,
            frequency_threshold=components.frequency_threshold,
            progress_callback=lambda percent, message: print(
                f"[{percent:3d}%] {message}"
            ),
            position_diagnostic_callback=writer.writerow,
        )
        try:
            pipeline.run()
        finally:
            components.laps.close()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Collect ACC minimap position diagnostics."
    )
    parser.add_argument("video", type=Path)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    if not args.video.is_file():
        parser.error(f"video not found: {args.video}")
    run_diagnostic(args.video, args.profile, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
