# Agent Handoff Documentation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the repository self-explaining through a tested documentation index, mandatory handoff rules, a current-status entry point, and an ACC PS5 plan aligned with the failed 2026-09-01 `s` validation.

**Architecture:** Active Markdown documents under `docs/` expose `summary` and `read_when` front matter. A dependency-free script lists that metadata while excluding working history by default; `AGENTS.md` makes the script and `docs/current-status.md` the mandatory entry path. No telemetry behavior changes in this plan.

**Tech Stack:** Python 3.13 standard library, zsh wrapper, Markdown/YAML-style front matter, `unittest`, Git

---

### Task 1: Add the tested documentation index

**Files:**
- Create: `scripts/docs_list.py`
- Create: `scripts/docs-list`
- Create: `tests/test_docs_list.py`

- [ ] **Step 1: Write focused failing tests**

Create `tests/test_docs_list.py` with temporary documentation trees. Cover default exclusion, explicit historical listing, front-matter parsing, and non-zero validation for malformed active documents:

```python
import importlib.util
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
                for path in self.docs_list.walk_markdown_files(root, include_all=True)
            ]

        self.assertEqual(files, ["archive/old.md", "current-status.md", "legacy/old.md"])

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
        self.assertEqual(metadata.read_when, ["starting any task", "changing priorities"])

    def test_validation_rejects_missing_front_matter(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "status.md").write_text("# Status\n", encoding="utf-8")

            errors = self.docs_list.validate_active_docs(root)

        self.assertEqual(errors, ["status.md: missing front matter"])


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_docs_list -v
```

Expected: import/loading failure because `scripts/docs_list.py` does not exist.

- [ ] **Step 3: Implement the dependency-free index**

Create `scripts/docs_list.py` with these public functions and behavior:

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
ALWAYS_EXCLUDED_DIRS = {"superpowers"}
HISTORICAL_DIRS = {"archive", "legacy"}


@dataclass(frozen=True)
class DocMetadata:
    summary: str
    read_when: list[str]


def walk_markdown_files(root: Path, *, include_all: bool = False) -> list[Path]:
    files = []
    for path in root.rglob("*.md"):
        relative = path.relative_to(root)
        if any(part.startswith(".") for part in relative.parts):
            continue
        if any(part in ALWAYS_EXCLUDED_DIRS for part in relative.parts):
            continue
        if not include_all and any(part in HISTORICAL_DIRS for part in relative.parts):
            continue
        files.append(path)
    return sorted(files, key=lambda path: path.relative_to(root).as_posix())


def extract_metadata(path: Path) -> tuple[DocMetadata | None, str | None]:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---\n"):
        return None, "missing front matter"
    end_index = content.find("\n---\n", 4)
    if end_index == -1:
        return None, "unterminated front matter"

    summary = None
    read_when = []
    in_read_when = False
    for raw_line in content[4:end_index].splitlines():
        line = raw_line.strip()
        if line.startswith("summary:"):
            summary = line.split(":", 1)[1].strip().strip("'\"")
            in_read_when = False
        elif line.startswith("read_when:"):
            in_read_when = True
        elif in_read_when and line.startswith("- "):
            read_when.append(line[2:].strip())
        elif line:
            in_read_when = False

    if not summary:
        return None, "summary is missing or empty"
    if not read_when:
        return None, "read_when is missing or empty"
    return DocMetadata(summary=summary, read_when=read_when), None


def validate_active_docs(root: Path) -> list[str]:
    errors = []
    for path in walk_markdown_files(root):
        _, error = extract_metadata(path)
        if error:
            errors.append(f"{path.relative_to(root).as_posix()}: {error}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="List ACC telemetry documentation metadata.")
    parser.add_argument("--all", action="store_true", help="include legacy and archive docs")
    args = parser.parse_args(argv)

    errors = validate_active_docs(DOCS_DIR)
    for path in walk_markdown_files(DOCS_DIR, include_all=args.all):
        relative = path.relative_to(DOCS_DIR).as_posix()
        metadata, error = extract_metadata(path)
        if error:
            print(f"{relative} - [{error}]")
            continue
        print(f"{relative} - {metadata.summary}")
        print(f"  Read when: {'; '.join(metadata.read_when)}")

    if errors:
        print("\nActive documentation metadata errors:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Create executable wrapper `scripts/docs-list`:

```zsh
#!/bin/zsh
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$script_dir/docs_list.py" "$@"
```

- [ ] **Step 4: Run focused tests and confirm GREEN**

Run:

```bash
chmod +x scripts/docs-list scripts/docs_list.py
PYTHONPATH=src .venv/bin/python -m unittest tests.test_docs_list -v
```

Expected: four tests pass.

- [ ] **Step 5: Commit the index implementation**

```bash
git add scripts/docs-list scripts/docs_list.py tests/test_docs_list.py
git commit -m "feat: add dynamic documentation index"
```

### Task 2: Establish the active handoff entry path

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/architecture.md`
- Modify: `docs/product-context.md`
- Modify: `docs/acc-ps5-plan.md`
- Create: `docs/current-status.md`
- Modify: `tests/test_repository_layout.py`

- [ ] **Step 1: Add failing repository-policy assertions**

Extend `test_current_documentation_is_complete_and_not_stale` in `tests/test_repository_layout.py` to assert:

```python
self.assertTrue((ROOT / "docs" / "current-status.md").exists())
self.assertTrue((ROOT / "scripts" / "docs-list").exists())
self.assertIn("./scripts/docs-list", (ROOT / "AGENTS.md").read_text())
self.assertIn("docs/current-status.md", (ROOT / "AGENTS.md").read_text())
```

Add a test that imports `scripts/docs_list.py` and asserts `validate_active_docs(ROOT / "docs") == []`.

- [ ] **Step 2: Run the policy tests and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_repository_layout -v
```

Expected: failure because `docs/current-status.md`, the AGENTS workflow, and active front matter are missing.

- [ ] **Step 3: Add front matter to every active document**

Use these headers:

```yaml
# docs/current-status.md
---
summary: single source of truth for current project state, active work, blockers, and exact next action
read_when:
  - starting any task
  - resuming work after another agent
  - changing project priorities or milestone status
---

# docs/architecture.md
---
summary: current code boundaries, dependency flow, telemetry contract, and adapter responsibilities
read_when:
  - changing package boundaries or data flow
  - modifying extraction, normalization, domain, application, visualization, or adapters
---

# docs/product-context.md
---
summary: Road to Verstappen product purpose and pilot coaching principles
read_when:
  - making product or coaching trade-offs
  - deciding whether a feature improves driver progression
---

# docs/acc-ps5-plan.md
---
summary: durable ACC PS5 telemetry roadmap, reliability stage gates, and blocked downstream coaching work
read_when:
  - working on ACC PS5 telemetry reliability
  - changing s, lap transitions, quality, segmentation, or coaching priorities
---
```

- [ ] **Step 4: Create the living current status**

Create `docs/current-status.md` containing:

- last verified date `2026-09-02`;
- current HEAD before this documentation sequence and the new documentation commits;
- confirmed working capture/control capabilities;
- exact `s` failure evidence from both ignored local session manifests;
- confirmed long-capture false lap transitions;
- modeled-but-not-propagated quality status;
- `active_milestone: repository handoff documentation`;
- `active_plan: docs/superpowers/plans/2026-09-02-agent-handoff-documentation.md`;
- downstream ACC development marked `blocked_pending_review`;
- exact next action: complete documentation verification and review with Loïc.

Do not link ignored session files as portable repository dependencies. Record their repository-relative local paths and state explicitly that they may be absent on another machine.

- [ ] **Step 5: Add the mandatory workflow to AGENTS.md**

Add sections requiring agents to:

1. read `AGENTS.md`;
2. run `./scripts/docs-list`;
3. always read `docs/current-status.md`;
4. select further docs from `read_when` hints;
5. inspect the active plan, Git status, and recent commits;
6. update status and plan checkboxes with verified facts before stopping;
7. commit one coherent concern at a time and leave no unexplained tracked changes.

State that repository documentation is durable memory and chat history is only short-term context.

- [ ] **Step 6: Run focused tests and the index**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_docs_list tests.test_repository_layout -v
./scripts/docs-list
git diff --check
```

Expected: all focused tests pass; the index lists exactly the four active docs without metadata errors.

- [ ] **Step 7: Commit the complete discovery and handoff system**

```bash
git add AGENTS.md docs/current-status.md docs/architecture.md docs/product-context.md docs/acc-ps5-plan.md tests/test_repository_layout.py
git commit -m "docs: establish agent handoff protocol"
```

### Task 3: Align the durable ACC PS5 plan with real evidence

**Files:**
- Modify: `docs/acc-ps5-plan.md`
- Modify: `docs/current-status.md`
- Modify: `tests/test_repository_layout.py`

- [ ] **Step 1: Add failing truth assertions**

Require the active plan to contain these stable markers:

```python
plan = (ROOT / "docs" / "acc-ps5-plan.md").read_text()
self.assertIn("s_status: failed_validation", plan)
self.assertIn("88.033333", plan)
self.assertIn("50.027742", plan)
self.assertIn("initial_s_anchor", plan)
self.assertIn("false lap transitions", plan)
self.assertIn("quality propagation", plan)
self.assertIn("blocked", plan)
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_repository_layout -v
```

Expected: missing-marker failures against the stale plan language.

- [ ] **Step 3: Rewrite the current baseline and stage gates**

Update `docs/acc-ps5-plan.md` so it clearly states:

- capture hardware and basic channels are validated;
- `s_status: failed_validation`;
- the initial anchor and saturation evidence;
- long-capture false lap transitions;
- the gap between the existing quality model and active pipeline outputs;
- ordered priorities: trustworthy `s`, robust lap transitions, quality propagation;
- explicit exit criteria for each priority;
- corner segmentation and all coaching layers are blocked until the three gates pass;
- the first downstream milestone is one manually reviewed Spa corner.

Update `docs/current-status.md` to mark the repository documentation milestone complete and the ACC reliability milestone `awaiting_review`. Set `active_plan: none` until the technical plan is agreed after the requested review point.

- [ ] **Step 4: Run focused verification**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_repository_layout tests.test_docs_list -v
./scripts/docs-list
git diff --check
```

Expected: all tests pass and the index reports no metadata errors.

- [ ] **Step 5: Commit the product-state correction**

```bash
git add docs/acc-ps5-plan.md docs/current-status.md tests/test_repository_layout.py
git commit -m "docs: record ACC telemetry reliability blockers"
```

### Task 4: Final repository verification and review gate

**Files:**
- Modify only if verification exposes a documentation defect.

- [ ] **Step 1: Run the complete automated suite**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m compileall -q src scripts tests main.py run_server.py
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
./scripts/docs-list
git diff --check
```

Expected: compilation and all tests pass; the index exits zero; no whitespace errors.

- [ ] **Step 2: Verify repository state and atomic history**

Run:

```bash
git status --short --branch
git log --oneline origin/main..HEAD
```

Expected: no unexplained tracked changes. History shows separate commits for the design, dynamic-discovery design refinement, implementation plan, index implementation, handoff protocol, and ACC reliability status.

- [ ] **Step 3: Stop before telemetry implementation**

Report the current documentation entry points, verification evidence, commits, and unresolved technical priorities. Do not create or execute the detailed telemetry correction plan until Loïc and the agent review the updated repository state.
