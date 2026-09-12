# ACC Telemetry

Extract driving telemetry from Assetto Corsa Competizione PS5 recordings when native telemetry is unavailable. Only native 1920x1080 at exactly 60 FPS with constant cadence is accepted, using the ACC static full-map HUD and the `ps5_full_map_1080p` profile. Other formats are refused before frame extraction/OCR; historical artifacts remain readable.

This repository is the telemetry foundation for the future Road to Verstappen product. It deliberately separates video extraction, normalization, domain concepts, analysis, and presentation.

The first coaching target is one Spa corner: reliable measurements, an explained
reference, paired trajectory images, one exercise and a follow-up check. Metric
lateral distance `d` is deferred pending evidence that it would improve those
debriefs. See the [delivery roadmap](docs/coaching-implementation-roadmap.md).

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

For an automatic development trial on a complete video, add
`--measurement-mode automatic`. Supply no visibility annotation inputs in this mode;
compare the output to existing annotations afterward. Fresh extracted values retain
unverified visibility reasons, invalid readings remain missing and coaching stays
ineligible. The default `reviewed` mode is unchanged. See the
[automatic trial](docs/automatic-system-trial.md).

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
  use until the remaining coverage and field-quality gates pass. Its clean and
  crash-heavy representative validation gates pass.
- Legacy map-only position remains importable for compatibility; production CLI and
  web processing use `s_odometry`, `s_visual`, and `s_fused`.
- By default, modern speed requires [source-bound reviewed HUD visibility](docs/speed-visibility.md)
  (`--speed-visibility-json`); without it speed is missing. Admitted speed retains
  fresh OCR text and explicit gaps; legacy median/holding remains isolated.
  Pedal transitions remain unsmoothed. See [A8 evidence](docs/fresh-measurement-results.md).
- Lateral distance `d` remains future work.
- OCR and map observations can be missing or anomalous and must not be treated as unquestioned truth.
- A1/A2 preserve fresh lap evidence, confirmation timing and speed/gear/lap quality
  through CSV normalization. A3 requires [reviewed control visibility](docs/control-visibility.md)
  (`--visibility-json`); otherwise controls remain missing. A5 bounds comparisons and preserves API provenance/nulls. Independent video
  validation is implemented in A7; initial measurements fail Gate A. Diagnostic replay checks establish internal consistency, not independent
  spatial accuracy; see the technical audit before using comparisons for coaching.

Optional [versioned session artifacts](docs/session-artifacts.md) are available with
`--artifact-dir NEW_DIRECTORY`: raw observations, normalized samples, CSV and a
source/configuration manifest. These exports remain ineligible for coaching until
the independent reliability gate passes.

[Independent annotation preparation](docs/capture-annotations.md) is available via
`scripts/annotate_capture.py prepare` and `validate`. It produces unreviewed selection
sheets and native frame windows; human labels and an independent holdout are still
required before validating measurement accuracy.

Use `scripts/annotate_capture.py consolidate --approval APPROVAL.json ... --output NEW_DIR`
to collect scoped approved readings without inventing unreviewed fields or duplicating
frame counts. Holdout roles and explicitly reviewed HUD absence remain intact.

[A7 capture validation](docs/capture-validation.md) reads those labels and existing
`telemetry-v2` sessions without rerunning OCR: `scripts/validate_capture.py
--artifacts SESSION --annotations LABELS_JSON --output NEW_REPORT_JSON`. Missing
evidence stays `not_evaluated`; failed measurements keep coaching blocked.

The [signal treatment](docs/signal-treatment.md) preserves fresh admitted speed
readings and abrupt pedal inputs. The modern pipeline does not use the legacy speed
filter. Speed regression remains deferred. See the active
[admission plan](docs/plans/2026-09-09-admission-corrections.md).

The [complete incidents trial](docs/real-system-trial-results.md) provides a local
report with video-aligned examples and explicit missing coverage. It remains a
development demonstration; Gate A still blocks reliable coaching.

The current [local GPT coaching delivery plan](docs/plans/2026-09-12-local-gpt-coaching-delivery.md)
starts from the implemented extraction and specifies the missing portable dossier:
comparable passages, calculated metrics, visual evidence and an explained reference.
Its [readiness audit](docs/gpt-coaching-readiness-audit.md) and
[manual report trial](docs/gpt-coaching-report-trial.md) explain the concrete gaps.
The plan is not implemented yet; the inherited web interface is outside this work.

## Reference documents

- [Current status](docs/current-status.md)
- [Product context](docs/product-context.md)
- [Architecture](docs/architecture.md)
- [ACC PS5 plan](docs/acc-ps5-plan.md)
- [Technical audit and coaching proposal](docs/technical-audit-2026-09-05.md)
- [Implementation roadmap: reference-based corner coaching](docs/coaching-implementation-roadmap.md)
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

To generate an ignored progress-validation trace from a representative clip:

```bash
PYTHONPATH=src python scripts/diagnose_progress.py CLIP.mov \
  --profile ps5_full_map_1080p \
  --output-dir data/lab/generic-progress-check
```
