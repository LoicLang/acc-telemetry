"""Command-line adapter for one ACC telemetry extraction run."""

import argparse
from pathlib import Path
from typing import Sequence

from acc_telemetry.application.components import build_components
from acc_telemetry.application.config import ConfigurationError, load_settings
from acc_telemetry.application.pipeline import TelemetryPipeline
from acc_telemetry.visualization.interactive import InteractiveTelemetryVisualizer


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Extract telemetry from an ACC PS5 gameplay video."
    )
    parser.add_argument("video", type=Path, help="immutable source video")
    parser.add_argument(
        "--profile",
        default="ps5_full_map_720p",
        help="ROI profile from config/roi_config.yaml",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/output"),
        help="directory for generated CSV and HTML files",
    )
    parser.add_argument("--visibility-json", type=Path, help="reviewed control visibility spans")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if not args.video.is_file():
        _parser().error(f"video not found: {args.video}")

    try:
        settings = load_settings()
        components = build_components(
            str(args.video),
            args.profile,
            settings=settings,
            visibility_json=args.visibility_json,
            enable_performance_stats=True,
        )
    except (ConfigurationError, ValueError, OSError) as error:
        _parser().error(str(error))

    profile = settings.profile(args.profile)
    pipeline = TelemetryPipeline(
        visibility=components.visibility,
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
    print("Controls require reviewed visibility; TC/ABS remain unavailable. Coaching gate pending.")

    visualizer = InteractiveTelemetryVisualizer(output_dir=str(args.output))
    dataframe = visualizer.create_dataframe(result.records)
    csv_path = visualizer.export_csv(dataframe)
    html_path = visualizer.plot_telemetry(dataframe)
    print(f"CSV: {csv_path}")
    print(f"Report: {html_path}")
    return 0
