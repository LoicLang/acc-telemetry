# Contributing

## Environment

Use Python 3.10 or newer. Create a local environment and install the pinned dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Run commands from the repository root. Until the package is installed, expose the source tree with `PYTHONPATH=src`.

Before changing the repository, run `./scripts/docs-list`, read
`docs/current-status.md`, and follow the `read_when` hints for the task. If the status
names an active specification or plan, read it before implementation.

## Tests

Run a focused test while working, then the complete suite:

```bash
PYTHONPATH=src python -m unittest tests.test_video_sampling -v
PYTHONPATH=src python -m unittest discover -s tests -v
```

New behavior and bug fixes require a failing test first. Tests must not read or modify personal data under `data/sessions/`.

If active documentation changes, also run:

```bash
./scripts/docs-list
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

Do not mix large file moves, behavior changes, data migration, and documentation rewrites in one commit.

Update `docs/current-status.md` in the same commit whenever a behavior change alters
verified project truth, blockers, the active milestone, or the exact next action.
