# ACC Telemetry Repository Foundations Implementation Plan


**Goal:** Establish a durable ACC PS5 telemetry repository with explicit package boundaries, validated configuration, quality-aware normalized samples, representative fixtures, long-lived session storage, and concise operational documentation.

**Architecture:** Preserve the tested PS5 behavior while moving implementation modules beneath `src/acc_telemetry/`. Keep temporary compatibility modules so existing imports remain stable, then make CLI and FastAPI adapters depend on application-layer construction helpers. Store personal training artifacts outside Git in session folders indexed by a verified local catalog.

**Tech Stack:** Python 3.13, OpenCV, NumPy, pandas, PyYAML, Plotly, FastAPI, `unittest`, Git

---

### Task 1: Establish repository policy and data skeleton

**Files:**
- Create: `AGENTS.md`
- Create: `CONTRIBUTING.md`
- Create: `data/README.md`
- Modify: `.gitignore`
- Archive: `.agent/`, `.claude/`, `.cursor/`, `CLAUDE.md` under `docs/archive/agent-guidance/`

- [ ] **Step 1: Add a failing repository-layout test**

Create `tests/test_repository_layout.py` with assertions that the required policy files exist, raw-data patterns are ignored, and legacy agent guidance has no active root-level copy.

- [ ] **Step 2: Confirm the test fails**

Run: `python -m unittest tests.test_repository_layout -v`

Expected: failures for missing `AGENTS.md`, `CONTRIBUTING.md`, and `data/README.md`.

- [ ] **Step 3: Add concise policy files and archive legacy guidance**

`AGENTS.md` must state the active pipeline, forbid mutation of `data/**/raw`, require tests before commits, and cap each change at one coherent concern. `CONTRIBUTING.md` must document setup, tests, data zones, configuration, and commit conventions. `data/README.md` must describe `sessions/YYYY/YYYY-MM-DD_track_platform_purpose/{raw,interim,processed,reports}`, `lab`, `shared`, and `catalog.csv`.

Update `.gitignore` to ignore all local data under `data/sessions/`, `data/lab/`, `data/shared/`, and `data/catalog.csv`, while retaining `data/README.md` and versioned fixtures.

- [ ] **Step 4: Run the focused and baseline tests**

Run: `python -m unittest tests.test_repository_layout -v && python -m unittest discover -s tests -v`

Expected: repository-layout tests and all 40 baseline tests pass.

- [ ] **Step 5: Commit**

Commit: `chore: establish repository policies`

### Task 2: Create explicit Python package boundaries

**Files:**
- Create: `src/acc_telemetry/__init__.py`
- Create: `src/acc_telemetry/{application,analysis,domain,normalization,extraction,visualization,adapters}/__init__.py`
- Move implementation into: `src/acc_telemetry/extraction/`, `src/acc_telemetry/visualization/`, `src/acc_telemetry/adapters/web/`
- Create compatibility imports: `src/video_processor.py`, `src/telemetry_extractor.py`, `src/lap_detector.py`, `src/position_tracker_v2.py`, `src/template_matcher.py`, `src/interactive_visualizer.py`, `src/web/`

- [ ] **Step 1: Extend the layout test with import expectations**

Assert these imports succeed:

```python
from acc_telemetry.extraction.video import VideoProcessor
from acc_telemetry.extraction.controls import TelemetryExtractor
from acc_telemetry.extraction.laps import LapDetector
from acc_telemetry.extraction.position import PositionTrackerV2
from acc_telemetry.visualization.interactive import InteractiveTelemetryVisualizer
```

- [ ] **Step 2: Confirm the new import test fails**

Run: `PYTHONPATH=src python -m unittest tests.test_repository_layout -v`

Expected: `ModuleNotFoundError: No module named 'acc_telemetry'`.

- [ ] **Step 3: Move modules and add compatibility re-exports**

Use focused modules:

```text
extraction/video.py       <- video_processor.py
extraction/controls.py    <- telemetry_extractor.py
extraction/laps.py        <- lap_detector.py
extraction/position.py    <- position_tracker_v2.py
extraction/templates.py   <- template_matcher.py
visualization/interactive.py <- interactive_visualizer.py
adapters/web/             <- web package
```

Compatibility files contain only documented re-exports, for example:

```python
from acc_telemetry.extraction.video import VideoProcessor, evenly_spaced_frame_indices

__all__ = ["VideoProcessor", "evenly_spaced_frame_indices"]
```

- [ ] **Step 4: Update internal imports and verify both import surfaces**

Run: `PYTHONPATH=src python -m compileall -q src main.py run_server.py && PYTHONPATH=src python -m unittest discover -s tests -v`

Expected: compilation succeeds and all tests pass.

- [ ] **Step 5: Commit**

Commit: `refactor: define telemetry package boundaries`

### Task 3: Add validated configuration and component construction

**Files:**
- Create: `config/telemetry.yaml`
- Create: `src/acc_telemetry/application/config.py`
- Create: `src/acc_telemetry/application/components.py`
- Create: `tests/test_configuration.py`
- Modify: `src/acc_telemetry/adapters/web/services/processing.py`
- Modify: `main.py`

- [ ] **Step 1: Write failing validation and wiring tests**

Test a valid config, a missing section, an out-of-range HSV triplet, and component construction using configured `sample_count`, white bounds, `max_jump_per_frame`, and OCR speed delta.

- [ ] **Step 2: Confirm RED**

Run: `PYTHONPATH=src python -m unittest tests.test_configuration -v`

Expected: import failure for `acc_telemetry.application.config`.

- [ ] **Step 3: Add the versioned defaults**

`config/telemetry.yaml` contains current behavior-preserving defaults:

```yaml
position:
  frequency_threshold: 0.45
  max_jump_per_frame: 1.0
ocr:
  max_speed_delta_kmh: 20
  recovery_tolerance_kmh: 3
normalization:
  speed_min_kmh: 0
  speed_max_kmh: 400
  pedal_min_percent: 0
  pedal_max_percent: 100
```

Profile-specific ROI, white bounds, and sampling remain in `config/roi_config.yaml`.

- [ ] **Step 4: Implement strict loading and shared constructors**

`load_settings()` loads both YAML files, validates mappings/numeric ranges, and returns immutable settings dataclasses. `build_components(profile_name, fps)` creates extraction components for both CLI and web adapters so threshold wiring is not duplicated.

- [ ] **Step 5: Run tests**

Run: `PYTHONPATH=src python -m unittest tests.test_configuration -v && PYTHONPATH=src python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 6: Commit**

Commit: `refactor: validate telemetry configuration`

### Task 4: Introduce the domain and normalization contract

**Files:**
- Create: `src/acc_telemetry/domain/telemetry.py`
- Create: `src/acc_telemetry/normalization/samples.py`
- Create: `tests/fixtures/telemetry/acc_ps5_representative.csv`
- Create: `tests/test_normalization.py`

- [ ] **Step 1: Write failing contract tests**

Cover `s` conversion from `track_position`, missing OCR values, held/interpolated markers, an out-of-range speed anomaly, and fixture loading.

- [ ] **Step 2: Confirm RED**

Run: `PYTHONPATH=src python -m unittest tests.test_normalization -v`

Expected: import failure for `acc_telemetry.domain.telemetry`.

- [ ] **Step 3: Add the quality-aware model**

Implement:

```python
class QualityFlag(StrEnum):
    OBSERVED = "observed"
    MISSING = "missing"
    HELD = "held"
    INTERPOLATED = "interpolated"
    ANOMALOUS = "anomalous"

@dataclass(frozen=True)
class TelemetrySample:
    frame: int
    time_s: float
    s: float | None
    speed_kmh: float | None
    gear: int | None
    throttle_pct: float | None
    brake_pct: float | None
    steering: float | None
    quality: frozenset[QualityFlag]
    anomalies: tuple[str, ...] = ()
```

The fixture contains eight synthetic but schema-representative rows, including normal, missing, held, and impossible speed values. No real lap is claimed.

- [ ] **Step 4: Implement normalization without silent correction**

Convert legacy rows to domain samples, preserve missing values, attach anomaly reasons, and retain source values for diagnostics. Do not calculate lateral `d`.

- [ ] **Step 5: Run tests and commit**

Run: `PYTHONPATH=src python -m unittest tests.test_normalization -v && PYTHONPATH=src python -m unittest discover -s tests -v`

Commit: `feat: add quality-aware telemetry contract`

### Task 5: Make adapters use the application boundary

**Files:**
- Create: `src/acc_telemetry/application/pipeline.py`
- Create: `src/acc_telemetry/adapters/cli.py`
- Modify: `main.py`
- Modify: `src/acc_telemetry/adapters/web/services/processing.py`
- Create: `tests/test_application_pipeline.py`

- [ ] **Step 1: Write failing application tests**

Use fake video/extraction components to verify full-video sampling, sequential frame records, lap resets, progress callbacks, and closure on failure.

- [ ] **Step 2: Confirm RED**

Run: `PYTHONPATH=src python -m unittest tests.test_application_pipeline -v`

Expected: import failure for `acc_telemetry.application.pipeline`.

- [ ] **Step 3: Extract the shared orchestration**

`TelemetryPipeline` owns video opening, map sampling, sequential extraction, lap transition handling, and DataFrame creation. It accepts components and callbacks; it does not import FastAPI, prompt for input, or choose storage paths.

- [ ] **Step 4: Reduce adapters to I/O concerns**

The CLI selects a local video/profile and renders outputs. The FastAPI service validates requests, selects storage, calls `TelemetryPipeline`, and returns metadata. Root `main.py` becomes a compatibility launcher for `acc_telemetry.adapters.cli.main`.

- [ ] **Step 5: Verify and commit**

Run: `PYTHONPATH=src python -m unittest tests.test_application_pipeline tests.test_web_profile_selection -v && PYTHONPATH=src python -m unittest discover -s tests -v`

Commit: `refactor: share telemetry application pipeline`

### Task 6: Replace stale documentation with an operational set

**Files:**
- Rewrite: `README.md`
- Create: `docs/product-context.md`
- Create: `docs/architecture.md`
- Create: `docs/acc-ps5-plan.md`
- Create: `docs/legacy/README.md`
- Move historical docs to: `docs/legacy/`

- [ ] **Step 1: Add documentation checks**

Extend `tests/test_repository_layout.py` to check required documents, quick-start commands, `s`, imperfect passages, quality/anomalies, future `d`, and the absence of references to missing scripts.

- [ ] **Step 2: Confirm the checks fail**

Run: `PYTHONPATH=src python -m unittest tests.test_repository_layout -v`

Expected: failures for missing current documents and stale README commands.

- [ ] **Step 3: Write the current documentation**

README commands must exist in the repository and use `PYTHONPATH=src`. Architecture must match actual imports. The ACC PS5 plan must distinguish current `s` confidence from future lateral `d` and define imperfect-passage/anomaly treatment.

- [ ] **Step 4: Archive historical reports conservatively**

Move legacy feature announcements and diagnostic reports without deleting them. `docs/legacy/README.md` explains that they are historical and may not match current entry points.

- [ ] **Step 5: Verify links, tests, and commit**

Run: `PYTHONPATH=src python -m unittest tests.test_repository_layout -v && rg -n "generate_detailed_analysis.py|compare_laps.py|compare_laps_by_position.py" README.md docs --glob '!docs/legacy/**'`

Expected: tests pass and the stale-script search has no output.

Commit: `docs: align project guidance with current code`

### Task 7: Consolidate local training artifacts

**Local files (ignored by Git):**
- Create: `data/catalog.csv`
- Create: `data/sessions/2026/2026-08-30_spa_ps5_calibration/`
- Create: `data/sessions/2026/2026-08-30_spa_ps5_lap-analysis/`
- Create: `data/lab/2026-08-30_smoke-test/`

- [ ] **Step 1: Recompute the reviewed source inventory**

For the explicit ACC paths only, record source path, size, and SHA-256. Expected unique content: three videos and four CSV datasets.

- [ ] **Step 2: Copy one canonical file per digest**

Place videos in `raw/`, earlier extraction variants in `interim/`, preferred telemetry in `processed/`, and smoke/failure artifacts in `lab/`. Do not edit or transcode files.

- [ ] **Step 3: Create session metadata and catalog entries**

Each `session.yaml` records known date, game, platform, track, purpose, artifact paths, and unknown values explicitly as `null`. `catalog.csv` records session ID, artifact role, relative path, digest, byte size, and every legacy source path.

- [ ] **Step 4: Verify every source before deletion**

Recompute destination hashes and sizes. Assert every selected source digest has exactly one canonical destination and every legacy source path is present in the catalog.

- [ ] **Step 5: Delete only the verified original video and CSV paths**

Remove the explicit files from the two temporary ACC worktrees, the dated Codex output directory, and `/Users/loiclang/Documents/Projects/acc-ps5-full-map-telemetrie.csv`. Do not delete directories, HTML reports, debug images, OCR data, or files belonging to other projects.

- [ ] **Step 6: Re-run independent verification**

Confirm all canonical files exist and match the pre-deletion digests; confirm every explicit original path is absent.

No Git commit is needed because personal data and its catalog are ignored.

### Task 8: Final verification and cleanup evidence

**Files:**
- Modify only if verification finds a scoped defect.

- [ ] **Step 1: Run the complete verification suite**

Run:

```bash
PYTHONPATH=src python -m compileall -q src main.py run_server.py
PYTHONPATH=src python -m unittest discover -s tests -v
git diff --check
git status --short --branch
```

Expected: compilation succeeds, all tests pass, no whitespace errors, and no tracked changes remain.

- [ ] **Step 2: Check tracked/generated data policy**

Run: `git ls-files | rg '\.(mp4|avi|mov|html|png)$|^data/(sessions|lab|shared)/'`

Expected: no personal/generated artifact paths.

- [ ] **Step 3: Review atomic history**

Run: `git log --oneline upstream/main..HEAD`

Expected: design history followed by coherent repository-policy, package, configuration, domain, pipeline, and documentation commits.

- [ ] **Step 4: Record final handoff**

Report the final repository path, tests executed, unique data retained, originals removed, known limitations, and the next recommended product step without implementing it.
