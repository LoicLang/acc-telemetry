"""Repository policy and structure checks."""

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]


class TestRepositoryLayout(unittest.TestCase):
    def test_operational_policy_files_exist(self):
        for relative_path in ("AGENTS.md", "CONTRIBUTING.md", "data/README.md"):
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())

    def test_personal_data_zones_are_ignored(self):
        paths = (
            "data/catalog.csv",
            "data/sessions/2026/example/raw/session.mp4",
            "data/lab/example/telemetry.csv",
            "data/shared/tessdata/eng.traineddata",
        )
        result = subprocess.run(
            ["git", "check-ignore", "--stdin"],
            cwd=ROOT,
            input="\n".join(paths),
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(set(result.stdout.splitlines()), set(paths))

    def test_legacy_agent_guidance_is_archived(self):
        self.assertFalse((ROOT / "CLAUDE.md").exists())
        for relative_path in (".agent", ".claude", ".cursor"):
            with self.subTest(path=relative_path):
                self.assertFalse((ROOT / relative_path).exists())


if __name__ == "__main__":
    unittest.main()
