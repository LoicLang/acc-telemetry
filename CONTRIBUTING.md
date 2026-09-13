# Contributing

## Environment

Use Python 3.10 or newer. Create a local environment and install the pinned dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run commands from the repository root. Until the package is installed, expose the source tree with `PYTHONPATH=src`.

Use [AGENTS.md](AGENTS.md) for working rules. Read `docs/current-status.md` and inspect
Git when starting work unless that context is already current. Use `./scripts/docs-list`
and the active plan/specification as needed; do not repeat reads without a reason.

## Active delivery

The owner-approved first milestone is the experimental `session_coaching.md` export
from existing local artifacts. Follow [current status](docs/current-status.md) and its
single active plan/specification. Gate A remains failed and artifact eligibility stays
false; complete general qualification is not a prerequisite for this limited export.
Use only locally supported facts with reasons and uncertainty. Do not restart old
counter campaigns, web work or obsolete plans from the archive.

## Proportionate verification

Choose checks that address the actual risk:

- Documentation: reread the change; check links/references when affected. No tests
  for trivial text edits. Check routing for moved/deleted documents.
- Localized behavior: focused tests; add a regression when it protects meaningful behavior.
- Pipeline/data-contract changes, broad refactoring or significant uncertainty:
  focused checks and the full suite when warranted.

There is no mandatory full suite per commit and no universal failing-test-first rule.
Do not repeat passing checks without a relevant change or failure. Tests must not modify
personal captures. Run `./scripts/docs-list` when document discovery/structure changes.

Commands available when appropriate:

```bash
PYTHONPATH=src python -m unittest tests.test_video_sampling -v
PYTHONPATH=src python -m unittest discover -s tests -v
```

## Data

- `raw/`: immutable source captures and exports.
- `interim/`: reproducible extraction artifacts.
- `processed/`: normalized telemetry.
- `reports/`: generated visual and written analysis.
- `tests/fixtures/`: small synthetic or explicitly reviewed samples safe for Git.

Personal data and the local catalog are ignored by Git. Never overwrite a raw file. When migrating data, compare byte size and SHA-256 before deleting an original.

## Configuration

HUD geometry and profile-specific parameters live in `config/roi_config.yaml`. Shared extraction and normalization thresholds live in `config/telemetry.yaml`. Validate configuration before processing a video.

## Commits

Use small, descriptive commits such as:

```text
refactor: define telemetry package boundaries
test: cover anomalous normalized samples
docs: explain ACC PS5 position quality
```

Group related changes coherently; separate migrations or unrelated changes when that
improves review or data safety. Small policy edits need only a review/diff check.

Update `docs/current-status.md` in the same commit whenever a behavior change alters
verified project truth, blockers, the active milestone, or the exact next action.
