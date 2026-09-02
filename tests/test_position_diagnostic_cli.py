"""Tests for the local position diagnostic CSV command."""

import csv
import tempfile
import unittest
from pathlib import Path


class TestPositionDiagnosticCLI(unittest.TestCase):
    def test_write_trace_creates_stable_csv_header(self):
        from scripts.diagnose_position import TRACE_FIELDS, write_trace

        row = {field: None for field in TRACE_FIELDS}
        row.update({"frame": 1, "time": 0.5, "decision": "observed"})

        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "trace.csv"
            write_trace(output, [row])
            with output.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))

        self.assertEqual(list(rows[0]), list(TRACE_FIELDS))
        self.assertEqual(rows[0]["frame"], "1")
        self.assertEqual(rows[0]["decision"], "observed")


if __name__ == "__main__":
    unittest.main()
