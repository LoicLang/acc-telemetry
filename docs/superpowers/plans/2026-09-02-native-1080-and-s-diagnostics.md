# Native 1080p and Position Diagnostics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Validate an explicit native 1080p ACC PS5 profile, measure its OCR value against the same frames downscaled to 720p, and expose a non-breaking diagnostic trace that identifies the first invalid `s` transition.

**Architecture:** Keep resolution support explicit in configuration. Make the existing OCR backend discover repository-local tessdata, then add extraction-local position diagnostics that legacy callers may ignore. Real-video evidence stays ignored under `data/lab/`; tracked tests use synthetic frames, paths, and fakes.

**Tech Stack:** Python 3.13, OpenCV, tesserocr, PyYAML, `unittest`, CSV, Git

---

### Task 1: Discover repository-local tessdata

**Files:**
- Modify: `src/acc_telemetry/extraction/laps.py`
- Modify: `tests/test_speed_ocr_mode.py`
- Modify: `docs/current-status.md`

- [x] **Step 1: Write a failing tessdata discovery test**

Add a test that creates `data/shared/tessdata/eng.traineddata` beneath a temporary project root and calls a new helper:

```python
def test_find_tessdata_path_prefers_repository_local_data(self):
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        tessdata = root / "data" / "shared" / "tessdata"
        tessdata.mkdir(parents=True)
        (tessdata / "eng.traineddata").write_bytes(b"fixture")

        result = find_tessdata_path(root)

    self.assertEqual(result, tessdata)
```

- [x] **Step 2: Run the focused test and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_speed_ocr_mode -v
```

Expected: import failure for `find_tessdata_path`.

- [x] **Step 3: Implement deterministic tessdata discovery**

Add:

```python
def find_tessdata_path(project_root: Path | None = None) -> Path | None:
    root = project_root or Path(__file__).parents[3]
    candidates = [
        root / "data" / "shared" / "tessdata",
        Path("/opt/homebrew/share/tessdata"),
        Path("/usr/share/tesseract-ocr/5/tessdata"),
        Path("/usr/share/tesseract-ocr/tessdata"),
        Path("/usr/share/tessdata"),
    ]
    for candidate in candidates:
        if (candidate / "eng.traineddata").is_file():
            return candidate
    return None
```

Use this helper in `LapDetector.__init__`. Pass `path=str(tessdata_path)` when found;
otherwise keep the existing default initialization and fallback behavior.

- [x] **Step 4: Verify the real backend**

Run:

```bash
PYTHONPATH=src .venv/bin/python - <<'PY'
from acc_telemetry.extraction.laps import LapDetector
detector = LapDetector()
assert detector._tesserocr_api is not None
detector.close()
PY
```

Expected: tesserocr initializes from `data/shared/tessdata`.

- [x] **Step 5: Update status and commit**

Record the verified local backend in `docs/current-status.md`, then run the focused
and full suites and commit:

```bash
git add src/acc_telemetry/extraction/laps.py tests/test_speed_ocr_mode.py docs/current-status.md
git commit -m "fix: discover repository OCR data"
```

### Task 2: Add the explicit 1080p profile

**Files:**
- Modify: `config/roi_config.yaml`
- Modify: `tests/test_ps5_profile.py`
- Modify: `tests/test_configuration.py`
- Modify: `docs/current-status.md`

- [x] **Step 1: Write failing profile tests**

Add an exact geometry test using this contract:

```python
expected_rois = {
    "throttle": {"x": 1758, "y": 1005, "width": 153, "height": 21},
    "brake": {"x": 1758, "y": 1025, "width": 153, "height": 18},
    "steering": {"x": 1703, "y": 993, "width": 201, "height": 14},
    "lap_number": {"x": 356, "y": 107, "width": 71, "height": 56},
    "lap_number_training": {"x": 272, "y": 107, "width": 71, "height": 56},
    "last_lap_time": {"x": 90, "y": 125, "width": 155, "height": 40},
    "speed": {"x": 1766, "y": 932, "width": 81, "height": 48},
    "gear": {"x": 1686, "y": 887, "width": 71, "height": 108},
    "track_map": {"x": 5, "y": 323, "width": 404, "height": 275},
}
```

The last-lap-time crop deliberately differs from a blind 1.5x scale: real frame
inspection shows the visible value around x=100..220, while the old scaled crop starts
at x=179 and truncates the time.

Also assert:

```python
profile = load_settings(ROOT).profile("ps5_full_map_1080p")
self.assertEqual(profile.sample_count, 60)
self.assertEqual(profile.white_lower, (0, 0, 150))
self.assertEqual(profile.white_upper, (180, 100, 255))
```

- [x] **Step 2: Run the profile tests and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_ps5_profile tests.test_configuration -v
```

Expected: missing `ps5_full_map_1080p`.

- [x] **Step 3: Add the configured profile**

Add `ps5_full_map_1080p` to `config/roi_config.yaml` with the exact regions above and:

```yaml
position_tracking:
  white_lower: [0, 0, 150]
  white_upper: [180, 100, 255]
  sample_count: 60
```

Do not change the 720p profile or automatic defaults.

- [x] **Step 4: Verify construction and selection**

Run the focused tests, then instantiate components with the new profile and assert
the video processor receives the 1080p regions.

- [x] **Step 5: Update status and commit**

Record profile availability without claiming OCR success. Run the full suite and
commit:

```bash
git add config/roi_config.yaml tests/test_ps5_profile.py tests/test_configuration.py docs/current-status.md
git commit -m "feat: add PS5 native 1080p profile"
```

### Task 3: Measure OCR on identical native and downscaled frames

**Files:**
- Local only: `data/lab/2026-09-02_native-1080-ocr/`
- Modify: `docs/current-status.md`
- Modify: `docs/acc-ps5-plan.md` only if the baseline decision changes

- [x] **Step 1: Create ignored evidence directories**

Create `native/`, `control-720p/`, and `reports/` below the local lab directory. Do
not copy or modify the source video.

- [x] **Step 2: Extract identical checkpoints**

Use the clean BMW source and timestamps after known lap crossings:

```text
300, 450, 600, 750, 900, 1050, 1200, 1500, 1800, 2100 seconds
```

For each timestamp, save one native PNG and one `1280x720` Lanczos downscale of the
same frame under the ignored lab directory.

- [x] **Step 3: Record visible ground truth**

Create ignored `reports/ground-truth.csv` with columns:

```text
timestamp_s,lap_number,last_lap_time,speed,gear
```

Read values from the native frame. Use an empty field when a HUD value is genuinely
not displayed; do not infer it.

- [x] **Step 3a: Calibrate OCR regions and preprocessing from RED tests**

Real-frame sampling established two concrete gaps in the seeded profile:

- use `lap_number_training: {x: 270, y: 105, width: 58, height: 60}`;
- use `last_lap_time: {x: 100, y: 128, width: 130, height: 34}`;
- threshold the lap-number crop at 200 and enlarge it 3x before tesserocr, matching
  the proven lap-time preprocessing pattern.

Update the exact profile tests and add a lap-number preprocessing test before changing
configuration or production OCR behavior. Commit calibration and preprocessing as
separate coherent changes.

- [x] **Step 4: Run both profiles**

For each checkpoint, instantiate a fresh `LapDetector`. Feed the same frame 15 times
for lap-number consensus, then record lap number, last-lap time, speed, and gear.
Write ignored `reports/ocr-results.csv` with `resolution`, `profile`, timestamp,
expected values, actual values, and exact-match booleans.

- [x] **Step 5: Decide the capture baseline**

Compute exact-match totals. Mark 1080p validated only if all configured regions are
visually correct, map extraction succeeds on sampled frames, and OCR is measurably
better or more complete than the downscaled control. Otherwise keep 1080p as a
supported experimental profile and document the failing fields.

- [x] **Step 6: Commit only the durable conclusion**

Update current status and, if warranted, the durable ACC plan. Run documentation and
full tests. Never commit frames, videos, or full OCR reports.

```bash
git add docs/current-status.md docs/acc-ps5-plan.md
git commit -m "docs: record native 1080 OCR evaluation"
```

Omit an unchanged file from `git add`.

### Task 4: Expose non-breaking position diagnostics

**Files:**
- Modify: `src/acc_telemetry/extraction/position.py`
- Modify: `tests/test_position_tracker_v2.py`

- [x] **Step 1: Write failing diagnostic-contract tests**

Define the intended extraction-local contract in tests:

```python
diagnostic = tracker.get_last_position_diagnostic()
self.assertEqual(diagnostic.dot_position, (20, 0))
self.assertEqual(diagnostic.closest_idx, 20)
self.assertEqual(diagnostic.start_idx, 10)
self.assertEqual(diagnostic.start_source, "lap_transition")
self.assertEqual(diagnostic.raw_position, 2.5)
self.assertFalse(diagnostic.completion_forced)
self.assertEqual(diagnostic.validated_position, 2.5)
self.assertEqual(diagnostic.decision, PositionDecision.OBSERVED)
```

Add focused cases for `LAP_RESET`, `MISSING_HELD`, `BACKWARD_HELD`, `JUMP_CLAMPED`,
`SMOOTHED`, and `FORCED_COMPLETION`. Existing numeric behavior assertions remain.

- [x] **Step 2: Run the tests and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_position_tracker_v2 -v
```

Expected: missing `PositionDecision` and `get_last_position_diagnostic`.

- [x] **Step 3: Add the diagnostic types**

Add extraction-local immutable types:

```python
class PositionDecision(StrEnum):
    NOT_READY = "not_ready"
    LAP_RESET = "lap_reset"
    OBSERVED = "observed"
    MISSING_HELD = "missing_held"
    BACKWARD_HELD = "backward_held"
    JUMP_CLAMPED = "jump_clamped"
    SMOOTHED = "smoothed"
    FORCED_COMPLETION = "forced_completion"


@dataclass(frozen=True)
class PositionDiagnostic:
    dot_position: tuple[int, int] | None
    closest_idx: int | None
    start_idx: int
    start_source: str
    travel_direction: int | None
    raw_position: float | None
    completion_forced: bool
    validated_position: float
    decision: PositionDecision
```

Track `start_source` as `geometric`, `lap_transition`, or `unavailable`. Store the
latest diagnostic after every `extract_position` call.

- [x] **Step 4: Refactor calculation without changing numeric behavior**

Extract a closest-index helper and a validation helper returning `(value, decision)`.
Keep `calculate_position()` and `_validate_position()` as compatibility wrappers.
`extract_position()` records raw projection before completion handling and the final
decision afterward.

- [x] **Step 5: Verify compatibility and commit**

Run position tests and the full suite. Commit only position code and tests:

```bash
git add src/acc_telemetry/extraction/position.py tests/test_position_tracker_v2.py
git commit -m "feat: expose position tracking diagnostics"
```

### Task 5: Collect a position trace through the shared pipeline

**Files:**
- Modify: `src/acc_telemetry/application/pipeline.py`
- Modify: `tests/test_application_pipeline.py`
- Create: `scripts/diagnose_position.py`
- Create: `tests/test_position_diagnostic_cli.py`

- [x] **Step 1: Write failing callback and CSV tests**

Add an optional pipeline callback:

```python
position_diagnostic_callback=lambda row: captured.append(row)
```

Assert one row contains frame, time, confirmed lap number, track position, and every
field from `PositionDiagnostic`. Assert no callback is required for existing callers.

Test that the diagnostic CLI writes a CSV header containing:

```text
frame,time,lap_number,track_position,dot_x,dot_y,closest_idx,start_idx,start_source,travel_direction,raw_position,completion_forced,validated_position,decision
```

- [x] **Step 2: Run the focused tests and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_application_pipeline tests.test_position_diagnostic_cli -v
```

Expected: unsupported callback and missing diagnostic CLI.

- [x] **Step 3: Implement the optional callback**

Add `position_diagnostic_callback` to `TelemetryPipeline.__init__`. After each final
position extraction for a frame, call it with a flat dictionary built from the latest
diagnostic. Do not add diagnostic columns to `PipelineResult.records`.

- [x] **Step 4: Implement the diagnostic CLI**

`scripts/diagnose_position.py` accepts:

```text
video --profile PROFILE --output TRACE.csv
```

It loads settings, builds components, creates a `TelemetryPipeline` with the callback,
streams rows through `csv.DictWriter`, and closes the output with a context manager.
It writes no HTML report and never changes the source video.

- [x] **Step 5: Verify compatibility and commit**

Run focused and full tests, then commit:

```bash
git add src/acc_telemetry/application/pipeline.py tests/test_application_pipeline.py scripts/diagnose_position.py tests/test_position_diagnostic_cli.py
git commit -m "feat: add position diagnostic trace"
```

### Task 6: Identify the first invalid `s` transition

**Files:**
- Local only: `data/lab/2026-09-02_native-1080-position/`
- Modify: `docs/current-status.md`
- Modify: `docs/acc-ps5-plan.md` only if the root-cause statement changes
- Modify: `docs/superpowers/plans/2026-09-02-native-1080-and-s-diagnostics.md`

- [x] **Step 1: Run the clean-session diagnostic**

Run `scripts/diagnose_position.py` on the primary BMW capture with
`ps5_full_map_1080p`. Write the trace below the ignored local lab directory.

- [x] **Step 2: Locate the first bad state transition**

Measure:

- first non-zero position;
- first long plateau;
- first forced completion;
- first position at or above 99.9%;
- each confirmed lap reset;
- anchor source and direction before each event.

Trace backward to the first wrong raw projection, closest index, direction choice,
anchor choice, or red-dot detection. Separate the first cause from later monotonic
holding and forced-completion amplification.

- [x] **Step 3: Add the smallest passing characterization regression**

Encode the confirmed first bad transition in `tests/test_position_tracker_v2.py` or
`tests/test_application_pipeline.py`. Name the specific incorrect decision and assert
that the diagnostic exposes it, for example `PositionDecision.FORCED_COMPLETION` plus
the wrong anchor source. The test must pass against current behavior so the repository
remains green; the next production-fix plan will replace the characterized outcome
with the desired expectation through a new red-green cycle.

- [x] **Step 4: Stop before the production fix**

Record the desired future assertion and the evidence required to make the
characterization test obsolete. Do not alter position behavior in this milestone.

- [x] **Step 5: Update durable status and commit**

Record measured evidence, confirmed root cause or remaining single hypothesis, and
the next exact correction. Mark this plan complete and set active plan to none.
Run all existing tests and documentation checks, then commit only durable documents:

```bash
git add docs/current-status.md docs/acc-ps5-plan.md docs/superpowers/plans/2026-09-02-native-1080-and-s-diagnostics.md
git commit -m "docs: record initial position root cause"
```

Omit unchanged files from `git add`.

### Task 7: Final verification and review gate

**Files:**
- Modify only if verification exposes a scoped defect.

- [x] **Step 1: Run complete verification**

```bash
PYTHONPATH=src .venv/bin/python -m compileall -q src scripts tests main.py run_server.py
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
./scripts/docs-list
git diff --check
git status --short --branch
git log --oneline origin/main..HEAD
```

- [x] **Step 2: Report and stop**

Report the 1080p OCR comparison, the first invalid `s` transition, test evidence,
commits, and unverified risks. Do not implement the production `s` correction, robust
lap-transition logic, quality propagation, segmentation, or coaching.
