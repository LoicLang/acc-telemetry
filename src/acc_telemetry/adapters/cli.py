"""Command-line adapter for one ACC telemetry extraction run."""

import argparse
from pathlib import Path
from typing import Sequence

from acc_telemetry.application.components import build_components
from acc_telemetry.application.config import ConfigurationError, load_settings
from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.application.session_artifacts import (
    check_destination, source_identity, write_session_artifacts,
)
from acc_telemetry.visualization.interactive import InteractiveTelemetryVisualizer


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract telemetry from an ACC PS5 gameplay video."
    )
    parser.add_argument("video", type=Path, help="immutable source video")
    parser.add_argument(
        "--profile",
        default="ps5_full_map_1080p",
        help="ROI profile from config/roi_config.yaml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/output"),
        help="directory for generated CSV and HTML files",
    )
    parser.add_argument("--measurement-mode", choices=("reviewed", "automatic"), default="reviewed",
                        help="automatic extracts without annotations; validate its measurements separately")
    parser.add_argument("--visibility-json", type=Path, help="reviewed control visibility spans")
    parser.add_argument("--speed-visibility-json", type=Path, help="source-bound reviewed speed HUD visibility")
    parser.add_argument("--artifact-dir", type=Path, help="new telemetry-v2 session directory")
    parser.add_argument("--clip-source-id", help="parent source identifier for a derived clip")
    parser.add_argument("--clip-start-s", type=float, default=0.0, help="clip start in parent seconds")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.video.is_file():
        _parser().error(f"video not found: {args.video}")

    try:
        if args.measurement_mode == "automatic" and (args.visibility_json or args.speed_visibility_json):
            raise ValueError("automatic extraction uses annotations only for later validation")
        source_before = None
        if args.artifact_dir is not None:
            target = check_destination(args.artifact_dir, args.video)
            if target == args.output.resolve() or target in args.output.resolve().parents:
                raise ValueError("legacy reports must remain outside the artifact directory")
            source_before = source_identity(args.video)
        if args.clip_start_s != 0 and not args.clip_source_id:
            raise ValueError("--clip-start-s requires --clip-source-id")
        settings = load_settings()
        components = build_components(
            str(args.video),
            args.profile,
            settings=settings,
            visibility_json=args.visibility_json,
            speed_visibility_json=args.speed_visibility_json,
            enable_performance_stats=True,
        )
    except (ConfigurationError, ValueError, OSError) as error:
        _parser().error(str(error))

    profile = settings.profile(args.profile)
    pipeline = TelemetryPipeline(
        settings=settings,
        measurement_mode=args.measurement_mode,
        visibility=components.visibility,
        speed_visibility=components.speed_visibility,
        video=components.video,
        controls=components.controls,
        laps=components.laps,
        progress=components.progress,
        has_track_map="track_map" in profile.rois,
        sample_count=components.sample_count,
        frequency_threshold=components.frequency_threshold,
        progress_callback=lambda percent, message: print(f"[{percent:3d}%] {message}"),
    )
    result = pipeline.run()
    if args.artifact_dir is not None:
        output = write_session_artifacts(result, args.artifact_dir, source_path=args.video,
            source_before=source_before, profile=args.profile,
            clip_origin=({"source_id": args.clip_source_id, "start_s": args.clip_start_s}
                         if args.clip_source_id else None))
        print(f"Session artifacts: {output}")
    print(f"Measurement mode: {args.measurement_mode}; extracted does not mean independently verified. TC/ABS unavailable; coaching gate pending.")

    visualizer = InteractiveTelemetryVisualizer(output_dir=str(args.output))
    dataframe = visualizer.create_dataframe(result.records)
    csv_path = visualizer.export_csv(dataframe)
    html_path = visualizer.plot_telemetry(dataframe, title=(
        "Automatic extraction — unverified" if args.measurement_mode == "automatic"
        else "ACC Telemetry Analysis"))
    print(f"CSV: {csv_path}")
    print(f"Report: {html_path}")
    return 0
