# ACC Telemetry

Extract driving telemetry from Assetto Corsa Competizione PS5 recordings when native telemetry is unavailable. The validated capture baseline is native 1920x1080 at 60 FPS with the ACC static full-map HUD and the `ps5_full_map_1080p` profile. Historical 720p recordings remain supported.

This repository is the telemetry foundation for the future Road to Verstappen product. It deliberately separates video extraction, normalization, domain concepts, analysis, and presentation.

## Quick start

Prerequisites: Python 3.10 or newer and Tesseract OCR. On macOS, install Tesseract with `brew install tesseract`.

```bash
cd /Users/loiclang/Documents/Projet/acc-telemetry
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Place an immutable recording in a session `raw/` directory, then run:

```bash
PYTHONPATH=src python main.py \
  data/sessions/2026/example_spa_ps5_session/raw/session-1080p60.mov \
  --profile ps5_full_map_1080p \
  --output data/sessions/2026/example_spa_ps5_session/processed
```

The command never writes into `raw/`. It writes a telemetry CSV and HTML report to the
chosen output directory. Modern CSV rows expose `s_odometry`, `s_visual`, `s_fused`,
uncertainty, source, and reasons. `track_position` remains a compatibility percentage
derived only from available `s_fused`.

## Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
```

The suite uses small versioned fixtures. It does not need or modify personal recordings.

## Data organization

Long-lived training data lives in `data/sessions/YYYY/YYYY-MM-DD_track_platform_purpose/`:

```text
raw/        original immutable capture
interim/    reproducible extraction artifacts
processed/  normalized telemetry
reports/    visual and written analysis
```

Experiments and failed extractions belong in `data/lab/`. Reusable local OCR resources belong in `data/shared/`. Personal data and `data/catalog.csv` are ignored by Git. See [data/README.md](data/README.md).

## Project map

```text
config/                         validated ROI and telemetry settings
src/acc_telemetry/extraction/   video, controls, OCR, track position
src/acc_telemetry/normalization quality and anomaly handling
src/acc_telemetry/domain/       stable telemetry concepts
src/acc_telemetry/analysis/     driving analysis boundary
src/acc_telemetry/application/  shared processing pipeline
src/acc_telemetry/visualization CSV and HTML output
src/acc_telemetry/adapters/     CLI and FastAPI entry points
tests/                          unit tests and small fixtures
```

Compatibility modules under `src/` keep older imports working during the migration.

## Current constraints

- ACC console video, not native PC telemetry.
- ROI profiles are resolution and HUD dependent.
- The full static minimap is supported; the scrolling minimap is not.
- The generic fused progress pipeline is implemented but remains blocked from coaching
  use until clean and crash-heavy real-session validation passes.
- Legacy map-only position remains importable for compatibility; production CLI and
  web processing use `s_odometry`, `s_visual`, and `s_fused`.
- Lateral distance `d` remains future work.
- OCR and map observations can be missing or anomalous and must not be treated as unquestioned truth.

## Reference documents

- [Current status](docs/current-status.md)
- [Product context](docs/product-context.md)
- [Architecture](docs/architecture.md)
- [ACC PS5 plan](docs/acc-ps5-plan.md)
- [Contribution rules](CONTRIBUTING.md)
- [Historical documentation](docs/legacy/README.md)

Agents discover active documentation through:

```bash
./scripts/docs-list
```

To run the API locally:

```bash
PYTHONPATH=src uvicorn acc_telemetry.adapters.web.main:app --reload
```
