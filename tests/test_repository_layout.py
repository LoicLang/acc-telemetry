"""Repository policy and structure checks."""

import subprocess
import unittest
from importlib import import_module
from pathlib import Path

from scripts.docs_list import validate_active_docs


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

    def test_repository_does_not_require_external_workflow_packages(self):
        legacy_skill_dir = "super" + "powers"
        self.assertFalse((ROOT / "docs" / legacy_skill_dir).exists())
        self.assertTrue((ROOT / "docs" / "plans").is_dir())
        self.assertTrue((ROOT / "docs" / "specs").is_dir())
        checked_paths = (
            ROOT / "AGENTS.md",
            ROOT / "README.md",
            ROOT / "CONTRIBUTING.md",
            ROOT / "scripts" / "docs_list.py",
            *(ROOT / "docs").rglob("*.md"),
        )
        for path in checked_paths:
            content = path.read_text(encoding="utf-8").lower()
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertNotIn(legacy_skill_dir, content)
                self.assertNotIn("required sub-skill", content)

    def test_public_package_boundaries_are_importable(self):
        imports = {
            "acc_telemetry.extraction.video": "VideoProcessor",
            "acc_telemetry.extraction.controls": "TelemetryExtractor",
            "acc_telemetry.extraction.laps": "LapDetector",
            "acc_telemetry.extraction.position": "PositionTrackerV2",
            "acc_telemetry.visualization.interactive": "InteractiveTelemetryVisualizer",
        }
        for module_name, symbol in imports.items():
            with self.subTest(module=module_name):
                module = import_module(module_name)
                self.assertTrue(hasattr(module, symbol))

    def test_root_cli_delegates_to_packaged_adapter(self):
        root_cli = import_module("main")
        packaged_cli = import_module("acc_telemetry.adapters.cli")
        self.assertIs(root_cli.main, packaged_cli.main)

    def test_server_launchers_use_packaged_web_adapter(self):
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        run_server = (ROOT / "run_server.py").read_text(encoding="utf-8")
        self.assertIn("ENV PYTHONPATH=/app/src", dockerfile)
        self.assertIn("acc_telemetry.adapters.web.main:app", dockerfile)
        self.assertIn("acc_telemetry.adapters.web.main:app", run_server)

    def test_current_documentation_is_complete_and_not_stale(self):
        required = (
            "README.md",
            "docs/current-status.md",
            "docs/video-data-audit.md",
            "docs/architecture.md",
            "docs/plans/video-to-agent-platform.md",
            "docs/legacy/README.md",
            "scripts/docs-list",
        )
        for relative_path in required:
            with self.subTest(path=relative_path):
                self.assertTrue((ROOT / relative_path).is_file())
        tracked_paths = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            capture_output=True,
            check=True,
            text=True,
        ).stdout.splitlines()
        self.assertIn("docs/architecture.md", tracked_paths)
        self.assertNotIn("docs/ARCHITECTURE.md", tracked_paths)

        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        for expected in ("python3 -m venv", "main.py", "unittest", "data/sessions"):
            with self.subTest(readme_contains=expected):
                self.assertIn(expected, readme)
        for stale_script in (
            "generate_detailed_analysis.py",
            "compare_laps.py",
            "compare_laps_by_position.py",
        ):
            with self.subTest(readme_excludes=stale_script):
                self.assertNotIn(stale_script, readme)

        agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("./scripts/docs-list", agents)
        self.assertIn("docs/current-status.md", agents)

    def test_active_documentation_has_routing_metadata(self):
        self.assertEqual(validate_active_docs(ROOT / "docs"), [])

    def test_current_docs_route_to_one_active_plan(self):
        import re
        status = (ROOT / "docs/current-status.md").read_text(encoding="utf-8")
        match = re.search(r"Active plan: `([^`]+)`", status)
        self.assertIsNotNone(match)
        self.assertTrue((ROOT / "docs" / match.group(1)).is_file())
        self.assertEqual(len(list((ROOT / "docs/plans").glob("*.md"))), 1)
        self.assertIn("Gate A: FAIL", status)
        self.assertIn("coaching_eligible=false", status)
        self.assertFalse((ROOT / "DEPLOY.md").exists())
        self.assertFalse((ROOT / "QUICKSTART_WEB.md").exists())

    def test_active_document_links_resolve(self):
        import re
        from urllib.parse import unquote
        from scripts.docs_list import walk_markdown_files
        paths = [ROOT / name for name in ("AGENTS.md", "README.md", "CONTRIBUTING.md")]
        paths += walk_markdown_files(ROOT / "docs")
        paths += list((ROOT / "docs/plans").glob("*.md"))
        paths += list((ROOT / "docs/specs").glob("*.md"))
        for path in paths:
            for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                if target.startswith(("https://", "http://", "mailto:", "#")):
                    continue
                local = unquote(target.split("#", 1)[0].strip("<>"))
                with self.subTest(document=path.relative_to(ROOT), target=local):
                    self.assertTrue((path.parent / local).exists())

    def test_current_docs_preserve_generic_progress_contract(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
        self.assertIn("ps5_full_map_1080p", readme)
        self.assertIn("1920x1080", readme)
        for concept in ("s_odometry", "s_visual", "s_fused", "v * delta_t"):
            self.assertIn(concept, architecture)
        self.assertIn("Generic position estimation", architecture)


if __name__ == "__main__":
    unittest.main()
