"""Tests for the generic progress diagnostic command and metrics."""

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.diagnose_progress import (
    TRACE_FIELDS,
    summarize_trace,
    validate_output_paths,
    write_trace,
)


class TestProgressDiagnosticCLI(unittest.TestCase):
    def test_write_trace_uses_the_stable_progress_schema(self):
        row = {field: None for field in TRACE_FIELDS}
        row.update({"frame": 1, "time": 0.5, "source": "predicted"})

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "trace.csv"
            write_trace(output, [row])
            with output.open(encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))

        self.assertEqual(list(written[0]), list(TRACE_FIELDS))
        self.assertEqual(written[0]["source"], "predicted")

    def test_summarizes_boundaries_resets_jumps_completion_and_sources(self):
        rows = [
            {
                "frame": 0,
                "time": 0.0,
                "confirmed_lap_number": 8,
                "boundary_confirmed": True,
                "s_odometry": 0.0,
                "s_fused": 0.0,
                "source": "observed",
            },
            {
                "frame": 1,
                "time": 0.1,
                "confirmed_lap_number": 8,
                "boundary_confirmed": False,
                "s_odometry": 0.5,
                "s_fused": 0.5,
                "source": "fused",
            },
            {
                "frame": 2,
                "time": 0.2,
                "confirmed_lap_number": 8,
                "boundary_confirmed": False,
                "s_odometry": 0.7,
                "s_fused": 0.75,
                "source": "fused",
            },
            {
                "frame": 3,
                "time": 0.3,
                "confirmed_lap_number": 8,
                "boundary_confirmed": False,
                "s_odometry": 0.5,
                "s_fused": 0.999,
                "source": "predicted",
            },
            {
                "frame": 4,
                "time": 0.4,
                "confirmed_lap_number": 8,
                "boundary_confirmed": False,
                "s_odometry": 1.0,
                "s_fused": 0.02,
                "source": "predicted",
            },
        ]

        summary = summarize_trace(rows)

        self.assertEqual(summary["confirmed_boundary_count"], 1)
        self.assertEqual(summary["premature_completion_count"], 1)
        self.assertEqual(summary["unconfirmed_reset_count"], 1)
        self.assertEqual(summary["nonlocal_visual_jump_count"], 3)
        self.assertEqual(summary["source_counts"], {"observed": 1, "fused": 2, "predicted": 2})

    def test_does_not_count_reappearance_after_missing_frames_as_a_jump(self):
        rows = [
            {"s_fused": 0.1, "boundary_confirmed": False},
            {"s_fused": None, "boundary_confirmed": False},
            {"s_fused": 0.8, "boundary_confirmed": False},
        ]

        summary = summarize_trace(rows)

        self.assertEqual(summary["nonlocal_visual_jump_count"], 0)

    def test_reports_checkpoint_spread_across_repeated_laps(self):
        rows = [
            {"confirmed_lap_number": 8, "s_odometry": 0.0, "s_fused": 0.0},
            {"confirmed_lap_number": 8, "s_odometry": 0.5, "s_fused": 0.500},
            {"confirmed_lap_number": 8, "s_odometry": 1.0, "s_fused": 1.0},
            {"confirmed_lap_number": 9, "s_odometry": 0.0, "s_fused": 0.0},
            {"confirmed_lap_number": 9, "s_odometry": 0.5, "s_fused": 0.501},
            {"confirmed_lap_number": 9, "s_odometry": 1.0, "s_fused": 1.0},
            {"confirmed_lap_number": 10, "s_odometry": 0.0, "s_fused": 0.0},
            {"confirmed_lap_number": 10, "s_odometry": 0.5, "s_fused": 0.499},
            {"confirmed_lap_number": 10, "s_odometry": 1.0, "s_fused": 1.0},
        ]

        summary = summarize_trace(rows)

        self.assertAlmostEqual(summary["max_checkpoint_spread"], 0.002)
        self.assertEqual(summary["comparable_checkpoint_count"], 99)

    def test_checkpoint_interpolation_is_not_biased_by_frame_density(self):
        rows = []
        for lap, repeated in ((8, 0.496), (9, 0.504)):
            rows.extend(
                [
                    {"confirmed_lap_number": lap, "s_odometry": 0.0, "s_fused": 0.0},
                    {"confirmed_lap_number": lap, "s_odometry": 0.495, "s_fused": 0.495},
                    *[
                        {"confirmed_lap_number": lap, "s_odometry": repeated, "s_fused": repeated}
                        for _ in range(8)
                    ],
                    {"confirmed_lap_number": lap, "s_odometry": 0.505, "s_fused": 0.505},
                    {"confirmed_lap_number": lap, "s_odometry": 1.0, "s_fused": 1.0},
                ]
            )

        summary = summarize_trace(rows)

        self.assertAlmostEqual(summary["max_checkpoint_spread"], 0.0)

    def test_refuses_any_output_that_resolves_to_the_input_video(self):
        with tempfile.TemporaryDirectory() as directory:
            video = Path(directory) / "session.mov"
            video.write_bytes(b"immutable")

            with self.assertRaisesRegex(ValueError, "input video"):
                validate_output_paths(video, video)


if __name__ == "__main__":
    unittest.main()
