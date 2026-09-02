"""Tests for dynamic documentation discovery."""

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_docs_list_module():
    spec = importlib.util.spec_from_file_location(
        "acc_docs_list", ROOT / "scripts" / "docs_list.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestDocsList(unittest.TestCase):
    def setUp(self):
        self.docs_list = load_docs_list_module()

    def test_default_excludes_history_and_working_plans(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (
                "current-status.md",
                "legacy/old.md",
                "archive/old.md",
                "superpowers/plans/work.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# document\n", encoding="utf-8")

            files = [
                path.relative_to(root).as_posix()
                for path in self.docs_list.walk_markdown_files(root)
            ]

        self.assertEqual(files, ["current-status.md"])

    def test_all_includes_history_but_not_superpowers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for relative in (
                "current-status.md",
                "legacy/old.md",
                "archive/old.md",
                "superpowers/specs/work.md",
            ):
                path = root / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("# document\n", encoding="utf-8")

            files = [
                path.relative_to(root).as_posix()
                for path in self.docs_list.walk_markdown_files(
                    root, include_all=True
                )
            ]

        self.assertEqual(
            files,
            ["archive/old.md", "current-status.md", "legacy/old.md"],
        )

    def test_extracts_summary_and_read_when(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "status.md"
            path.write_text(
                "---\nsummary: current project truth\nread_when:\n"
                "  - starting any task\n  - changing priorities\n---\n\n# Status\n",
                encoding="utf-8",
            )

            metadata, error = self.docs_list.extract_metadata(path)

        self.assertIsNone(error)
        self.assertEqual(metadata.summary, "current project truth")
        self.assertEqual(
            metadata.read_when,
            ["starting any task", "changing priorities"],
        )

    def test_validation_rejects_missing_front_matter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "status.md").write_text("# Status\n", encoding="utf-8")

            errors = self.docs_list.validate_active_docs(root)

        self.assertEqual(errors, ["status.md: missing front matter"])


if __name__ == "__main__":
    unittest.main()
