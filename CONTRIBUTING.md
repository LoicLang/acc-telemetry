# Contributing

## Environment

Use Python 3.12 or newer (the audited local environment is Python 3.13.2). Install
the system dependencies listed in the README first, then create a local environment
and install the pinned dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run commands from the repository root. Until the package is installed, expose the source tree with `PYTHONPATH=src`.

Use [AGENTS.md](AGENTS.md) for working rules. Read `docs/current-status.md` and inspect
Git when starting work unless that context is already current. Use `./scripts/docs-list`
and the active plan/specification as needed; do not repeat reads without a reason.

## Community handoff

The video research is paused as of17 September2026. The owner is moving to a separate
PC-based project; this repository is retained for anyone interested in continuing the
video approach. Read [current status](docs/current-status.md), the
[frozen roadmap](docs/plans/video-to-agent-platform.md) and
[capability audit](docs/video-data-audit.md). Do not interpret old next-action sections
as an obligation to restart model training or private-data experiments.

A fresh clone contains code and tests, not the local run datasets or model checkpoints.
Use `PYTHONPATH=src python scripts/demo_control_episodes.py` to inspect synthetic output,
then test your own compatible capture. Preserve unknowns and source/field provenance.
Review [origin and licensing status](NOTICE.md) before planning redistribution.

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
PYTHONPATH=src python -m unittest discover -s tests -p 'test_video_sampling.py' -v
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
the handoff status, verified behavior or known limits.
