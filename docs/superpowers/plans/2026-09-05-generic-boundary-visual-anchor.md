# Generic Boundary Visual Anchor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Retain compact imperfect red-dot observations and recover a visual centerline anchor around a confirmed lap boundary without permitting visual evidence to create or reset a lap.

**Architecture:** OpenCV extraction will broaden only the dimensionless shape evidence it retains; pure application code will choose an exact, interpolated, nearest, or missing boundary anchor from frame-aligned projections. The existing lap confirmer remains the only reset authority, while diagnostic output exposes anchor provenance and uncertainty. The new BMW replay and both representative controls remain the final acceptance gates.

**Tech Stack:** Python 3.13, NumPy, OpenCV, dataclasses, `unittest`, CSV/JSON diagnostics, Git

---

## Constraints and fixed decisions

- Work only on `fix/boundary-visual-anchor`; do not push.
- Treat all videos under `/Users/loiclang/Movies/` and `data/**/raw/` as immutable.
- Keep production rules free of circuit names, coordinates, templates, absolute pixel sizes, car models, and frame-rate-specific counts.
- A `ConfirmedLapBoundary` is the only event allowed to create or reset an anchor.
- Candidate extraction returns evidence; it never selects the true position.
- Exact projection wins over recovered projection. Ambiguity produces no anchor.
- A recovery search stops at another confirmed boundary and must pass both its time and normalized-odometry gates.
- Opening partial laps remain unanchored. Calibration remains boundary-to-boundary and rejects the same outliers as today.
- After each RED, confirm the failure is caused by the intended missing behavior. Before each commit, run focused tests and the full suite.
- Store replay output only under ignored `data/lab/`; never commit videos, frames, traces, or JSON reports.

## Planned file responsibilities

| File | Responsibility in this change |
| --- | --- |
| `config/telemetry.yaml` | Dimensionless compact-shape thresholds and bounded anchor-recovery gates. |
| `src/acc_telemetry/application/config.py` | Immutable validated settings, including cross-field ordering for one-sided versus bracketing gates. |
| `src/acc_telemetry/extraction/map_progress.py` | Basic red/color/area/shape evidence only. |
| `src/acc_telemetry/application/progress.py` | Pure boundary-anchor selection, wrapped interpolation, session integration, provenance, and uncertainty. |
| `src/acc_telemetry/application/pipeline.py` | Add anchor provenance to the existing diagnostic callback only. |
| `scripts/diagnose_progress.py` | Add the stable diagnostic column and anchor-source summary counts. |
| `tests/test_configuration.py` | Exact settings and invalid-threshold coverage. |
| `tests/test_map_progress.py` | Synthetic irregular-dot and false-positive shape regressions. |
| `tests/test_position_tracker_v2.py` | Update the characterization call to the expanded extraction contract. |
| `tests/test_progress_fusion.py` | Pure recovery rules plus end-to-end session anchoring regressions. |
| `tests/test_application_pipeline.py` | Frame-result and diagnostic propagation compatibility. |
| `tests/test_progress_diagnostic_cli.py` | Trace schema and anchor-source summary behavior. |
| `docs/current-status.md` | Verified implementation/replay result and exact next action. |
| `docs/acc-ps5-plan.md` | Change the `s` stage only if all three replay gates pass. |

### Task 1: Retain compact imperfect red-dot contours

**Files:**
- Modify: `config/telemetry.yaml`
- Modify: `src/acc_telemetry/application/config.py`
- Modify: `src/acc_telemetry/extraction/map_progress.py`
- Modify: `tests/test_configuration.py`
- Modify: `tests/test_map_progress.py`
- Modify: `tests/test_position_tracker_v2.py`

- [x] **Step 1: Write RED configuration tests for the new dimensionless thresholds**

Extend `progress.candidates` in `_telemetry_with_progress()` and assert the production
values load:

```python
"candidates": {
    "min_area_fraction": 0.00002,
    "max_area_fraction": 0.005,
    "min_circularity": 0.35,
    "min_compact_aspect_ratio": 0.75,
    "min_filled_extent": 0.45,
    "min_convex_compactness": 0.45,
},
```

Add each new key with values `0` and `1.1` to the invalid-case loop and require a
`ConfigurationError` naming the full key.

- [x] **Step 2: Run the configuration test and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_configuration.TestTelemetryConfiguration.test_loads_current_ps5_profile_and_shared_thresholds tests.test_configuration.TestTelemetryConfiguration.test_rejects_invalid_generic_progress_thresholds -v
```

Expected: FAIL because `CandidateSettings` and `load_settings()` do not expose the
three compact-shape fields.

- [x] **Step 3: Add and validate the candidate settings**

Extend the frozen settings type:

```python
@dataclass(frozen=True)
class CandidateSettings:
    min_area_fraction: float
    max_area_fraction: float
    min_circularity: float
    min_compact_aspect_ratio: float
    min_filled_extent: float
    min_convex_compactness: float
```

Load all three new values with `_fraction()` under `progress.candidates`, and add the
exact YAML values from Step 1. Do not add defaults in Python; missing versioned
configuration must fail explicitly.

- [x] **Step 4: Confirm configuration GREEN**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_configuration -v
```

Expected: all configuration and component-wiring tests pass.

- [x] **Step 5: Write RED contour tests for the measured failure shape**

Create a 16 by 16 compact jagged red polygon whose raw circularity is below `0.35`
but whose aspect ratio, filled extent, and convex compactness pass the new thresholds.
Assert it is retained. In the same test class, create an elongated bar, a sparse
concave fragment, a large block, and a one-pixel speck; assert none are retained.

Use this neutral 24-point star fixture for the accepted irregular contour. Its
measured properties are circularity `0.272`, aspect ratio `1.0`, filled extent
`0.457`, and convex compactness `0.665`:

```python
irregular_compact = np.array(
    [
        (28, 20), (25, 21), (27, 24), (24, 24),
        (24, 27), (21, 25), (20, 28), (19, 25),
        (16, 27), (16, 24), (13, 24), (15, 21),
        (12, 20), (15, 19), (13, 16), (16, 16),
        (16, 13), (19, 15), (20, 12), (21, 15),
        (24, 13), (24, 16), (27, 16), (25, 19),
    ],
    dtype=np.int32,
)
cv2.fillPoly(image, [irregular_compact], (0, 0, 255))
```

Use the same coordinates translated away from other fixtures. Build the rejected
sparse shape with the same outer box but inner points at radius `4`; it has filled
extent `0.360`, below the configured `0.45`.

Use one shared settings helper so every call supplies the complete contract:

```python
def _candidate_settings() -> dict[str, float]:
    return {
        "min_area_fraction": 0.00002,
        "max_area_fraction": 0.005,
        "min_circularity": 0.35,
        "min_compact_aspect_ratio": 0.75,
        "min_filled_extent": 0.45,
        "min_convex_compactness": 0.45,
    }
```

The positive assertion must also prove that the fixture exercises the alternate
path:

```python
self.assertLess(candidates[0].circularity, 0.35)
self.assertEqual(len(candidates), 1)
```

- [x] **Step 6: Run candidate tests and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_map_progress.TestRedDotCandidates -v
```

Expected: FAIL because `extract_red_candidates()` does not accept the three new
arguments and rejects the irregular compact contour under the current circularity
gate.

- [x] **Step 7: Implement the minimal alternate compact-shape path**

Extend `extract_red_candidates()` with required keyword-only parameters. After the
existing area check, calculate:

```python
x, y, width, height = cv2.boundingRect(contour)
aspect_ratio = min(width, height) / max(width, height)
filled_extent = area_px / float(width * height)
convex_hull = cv2.convexHull(contour)
convex_perimeter = float(cv2.arcLength(convex_hull, True))
convex_compactness = (
    0.0
    if convex_perimeter <= 0
    else 4.0 * pi * area_px / (convex_perimeter * convex_perimeter)
)
compact_shape = (
    aspect_ratio >= min_compact_aspect_ratio
    and filled_extent >= min_filled_extent
    and convex_compactness >= min_convex_compactness
)
if circularity < min_circularity and not compact_shape:
    continue
```

Keep the existing area, perimeter, moments, stable ordering, and `RedDotCandidate`
contract unchanged. Pass the three settings from `ProgressSessionEstimator.observe_frame()`
and update every direct test call, including the legacy characterization.

- [x] **Step 8: Run focused and full GREEN verification**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_configuration tests.test_map_progress tests.test_position_tracker_v2 tests.test_progress_fusion -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
```

Expected: focused tests and the complete suite pass; no whitespace errors.

- [x] **Step 9: Commit candidate retention atomically**

```bash
git add config/telemetry.yaml src/acc_telemetry/application/config.py src/acc_telemetry/extraction/map_progress.py src/acc_telemetry/application/progress.py tests/test_configuration.py tests/test_map_progress.py tests/test_position_tracker_v2.py
git commit -m "fix: retain compact red map candidates"
```

### Task 2: Recover a boundary anchor with pure bounded rules

**Files:**
- Modify: `config/telemetry.yaml`
- Modify: `src/acc_telemetry/application/config.py`
- Modify: `src/acc_telemetry/application/progress.py`
- Modify: `tests/test_configuration.py`
- Modify: `tests/test_progress_fusion.py`

- [x] **Step 1: Write RED settings tests for dual recovery gates**

Add this section to test configuration and production YAML:

```yaml
boundary_anchor:
  max_bracketing_gap_s: 0.25
  max_bracketing_distance_fraction: 0.005
  max_one_sided_gap_s: 0.10
  max_one_sided_distance_fraction: 0.002
```

Assert all values load through a frozen `BoundaryAnchorSettings`. Add invalid cases
for zero, negative, or greater-than-one distance fractions. Add cross-field tests
requiring each one-sided limit to be less than or equal to its bracketing counterpart.

- [x] **Step 2: Run settings tests and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_configuration.TestTelemetryConfiguration.test_loads_current_ps5_profile_and_shared_thresholds tests.test_configuration.TestTelemetryConfiguration.test_rejects_invalid_generic_progress_thresholds -v
```

Expected: FAIL because `ProgressSettings.boundary_anchor` is missing.

- [x] **Step 3: Implement the validated recovery settings**

Add:

```python
@dataclass(frozen=True)
class BoundaryAnchorSettings:
    max_bracketing_gap_s: float
    max_bracketing_distance_fraction: float
    max_one_sided_gap_s: float
    max_one_sided_distance_fraction: float
```

Load time values with `_positive()` and distance values with `_fraction()`. Reject:

```python
if boundary_anchor.max_one_sided_gap_s > boundary_anchor.max_bracketing_gap_s:
    raise ConfigurationError(
        "progress.boundary_anchor.max_one_sided_gap_s must not exceed "
        "progress.boundary_anchor.max_bracketing_gap_s"
    )
if (
    boundary_anchor.max_one_sided_distance_fraction
    > boundary_anchor.max_bracketing_distance_fraction
):
    raise ConfigurationError(
        "progress.boundary_anchor.max_one_sided_distance_fraction must not exceed "
        "progress.boundary_anchor.max_bracketing_distance_fraction"
    )
```

Add `boundary_anchor` to `ProgressSettings` and confirm the full configuration module
passes before writing recovery behavior.

- [x] **Step 4: Define the RED pure recovery contract**

Import these not-yet-existing application-local types in the test to fix their public
contract before implementation:

```python
class BoundaryAnchorSource(StrEnum):
    EXACT = "boundary_anchor_exact"
    INTERPOLATED = "boundary_anchor_interpolated"
    NEAREST = "boundary_anchor_nearest"
    MISSING = "boundary_anchor_missing"


@dataclass(frozen=True)
class AnchorFrameEvidence:
    time_s: float
    distance_m: float
    projections: tuple[VisualProjection, ...]
    boundary: ConfirmedLapBoundary | None


@dataclass(frozen=True)
class BoundaryVisualAnchor:
    raw_s: float | None
    centroid: tuple[float, float] | None
    uncertainty: float
    source: BoundaryAnchorSource
```

Write tests for a pure function with this signature:

```python
recover_boundary_visual_anchor(
    frames: tuple[AnchorFrameEvidence, ...],
    *,
    boundary_index: int,
    effective_lap_length_m: float,
    last_raw_s: float | None,
    max_centerline_distance_px: float,
    max_progress_error: float,
    min_score_margin: float,
    unavailable_uncertainty: float,
    settings: BoundaryAnchorSettings,
) -> BoundaryVisualAnchor
```

Cover these exact cases:

- one exact projection returns `EXACT`, its `raw_s`, and zero added uncertainty;
- `before=0.998`, `after=0.002`, and a halfway boundary returns approximately `0.0`
  with `INTERPOLATED`;
- odometry distances `100.0`, `102.0`, and `108.0` weight the same wrapped interval
  at `0.25`, rather than the timestamp midpoint;
- one projection within `0.10 s` and `0.002` lap distance returns `NEAREST` with
  uncertainty greater than exact;
- a projection outside either one-sided gate returns `MISSING`;
- a search stops when it encounters another non-target boundary;
- two equally plausible projection pairs return `MISSING` rather than selecting by
  tuple order.

- [x] **Step 5: Run pure recovery tests and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_progress_fusion.TestBoundaryVisualAnchor -v
```

Expected: FAIL because the recovery types and function do not exist.

- [x] **Step 6: Implement exact, bracketing, nearest, and missing selection**

Import `StrEnum` from `enum`, implement the three immutable types from Step 4 in
`progress.py`, then implement these private stages:

```python
def _wrapped01(value: float) -> float:
    return value % 1.0


def _distance_fraction(first: AnchorFrameEvidence, second: AnchorFrameEvidence, lap_length: float) -> float:
    return abs(second.distance_m - first.distance_m) / lap_length


def _inside_gap(frame: AnchorFrameEvidence, boundary: AnchorFrameEvidence, *, max_gap_s: float, max_distance_fraction: float, lap_length: float) -> bool:
    return (
        abs(frame.time_s - boundary.time_s) <= max_gap_s
        and _distance_fraction(frame, boundary, lap_length) <= max_distance_fraction
    )
```

For exact evidence, rank projections with a normalized lower-is-better score using
centerline distance and, when available, wrapped continuity from `last_raw_s`. Require
the best score to beat the second by `min_score_margin`; a single candidate is
unambiguous.

Scan outward for the closest non-empty frame on each side, stopping at another
boundary. For bracketing evidence, evaluate every before/after pair with:

```text
pair_error = abs(abs(wrapped_delta(after.raw_s, before.raw_s))
                 - normalized_odometric_distance)
pair_score = pair_error + before.distance_px / max_distance_px
                         + after.distance_px / max_distance_px
```

Require a unique winner by `min_score_margin`. Interpolate using odometric distance;
use elapsed time only when total odometric distance is zero. Calculate added
uncertainty as at most `0.25 * unavailable_uncertainty`, scaled by the larger consumed
bracketing gate fraction.

For one-sided evidence, require the stricter gates and the same unique projection
rule. Return its raw coordinate and add at most `0.50 * unavailable_uncertainty`,
scaled by the larger consumed one-sided gate fraction. Return `MISSING` with
`uncertainty=unavailable_uncertainty` when no unique bounded result exists.

- [x] **Step 7: Run focused and full GREEN verification**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_configuration tests.test_progress_fusion.TestBoundaryVisualAnchor -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
```

Expected: all recovery/configuration tests and the complete suite pass.

- [x] **Step 8: Commit pure anchor recovery atomically**

```bash
git add config/telemetry.yaml src/acc_telemetry/application/config.py src/acc_telemetry/application/progress.py tests/test_configuration.py tests/test_progress_fusion.py
git commit -m "feat: recover bounded boundary visual anchors"
```

### Task 3: Integrate anchor recovery and expose provenance

**Files:**
- Modify: `src/acc_telemetry/application/progress.py`
- Modify: `src/acc_telemetry/application/pipeline.py`
- Modify: `scripts/diagnose_progress.py`
- Modify: `tests/test_progress_fusion.py`
- Modify: `tests/test_application_pipeline.py`
- Modify: `tests/test_progress_diagnostic_cli.py`

- [ ] **Step 1: Write the RED session regression matching the real failure**

In `TestProgressSessionEstimator`, use a synthetic square centerline, two-observation
lap confirmation, and enough constant-speed frames for two complete boundaries. Put
valid red candidates immediately before and after the first boundary but pass a blank
ROI on the exact confirmation frame. Assert:

```python
self.assertEqual(
    result.frames[first_boundary_index].boundary_anchor_source,
    BoundaryAnchorSource.INTERPOLATED,
)
self.assertEqual(result.frames[first_boundary_index].estimate.s_fused, 0.0)
self.assertIsNotNone(result.frames[first_boundary_index + 2].estimate.s_visual)
self.assertEqual(result.frames[first_boundary_index + 2].estimate.source, ProgressSource.FUSED)
self.assertEqual(
    sum(frame.boundary is not None for frame in result.frames),
    2,
)
```

Add a companion case containing visually wrapped projections without a confirmed
boundary; assert no anchor source changes to exact/interpolated/nearest and no reset
occurs.

- [ ] **Step 2: Run the session regression and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_progress_fusion.TestProgressSessionEstimator -v
```

Expected: FAIL because `ProgressFrameResult` has no anchor provenance and `finalize()`
still initializes `raw_anchor_s` only from exact boundary-frame projections.

- [ ] **Step 3: Precompute frame projection evidence and integrate recovery**

In `ProgressSessionEstimator.finalize()`, construct one `AnchorFrameEvidence` per raw
frame after odometry and calibration are available. Call
`recover_boundary_visual_anchor()` only when `frame.lap_state.boundary` is not `None`.

On an exact/interpolated/nearest result:

```python
raw_anchor_s = anchor.raw_s
last_raw_s = anchor.raw_s
last_centroid = anchor.centroid
previous_displacement_px = None
direction = None
```

On `MISSING`, clear the visual anchor and direction so a stale prior-lap coordinate
cannot leak into the new lap. Do not promote a later ordinary projection to a boundary
without calling recovery for a confirmed boundary.

Extend the immutable frame result:

```python
@dataclass(frozen=True)
class ProgressFrameResult:
    frame: int
    raw_lap_number: int | None
    confirmed_lap_number: int | None
    boundary: ConfirmedLapBoundary | None
    boundary_confidence: float
    candidate_count: int
    selected_centroid: tuple[float, float] | None
    estimate: ProgressEstimate
    boundary_anchor_source: BoundaryAnchorSource | None = None
```

Non-boundary frames use `None`. Boundary frames always expose one of the four source
values.

- [ ] **Step 4: Propagate boundary reason and uncertainty through the fused estimator**

Extend `FusedProgressEstimator.update()` with a keyword-only optional anchor:

```python
def update(
    self,
    odometry: OdometryPoint,
    visual: VisualSelection,
    boundary: ConfirmedLapBoundary | None,
    *,
    boundary_anchor: BoundaryVisualAnchor | None = None,
) -> ProgressEstimate:
```

In the boundary branch, keep `s_fused == s_odometry == 0.0`. Add the anchor source to
the reasons and initialize uncertainty from the anchor:

```python
anchor_reason = (
    BoundaryAnchorSource.MISSING.value
    if boundary_anchor is None
    else boundary_anchor.source.value
)
self._uncertainty = (
    self.unavailable_uncertainty
    if boundary_anchor is None
    else boundary_anchor.uncertainty
)
reasons = ("lap_boundary_confirmed", anchor_reason)
```

An exact anchor remains `OBSERVED`. Interpolated and nearest anchors keep the boundary
coordinate at zero but use `INTERPOLATED` and `PREDICTED` source respectively. Missing
visual anchoring must not cancel the confirmed odometric zero; it reports
`boundary_anchor_missing` and existing uncertainty behavior.

- [ ] **Step 5: Run progress tests and confirm GREEN**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_progress_fusion -v
```

Expected: all pure fusion, recovery, and session tests pass; visual evidence still
cannot reset without a boundary.

- [ ] **Step 6: Write RED diagnostic provenance tests**

Update `FakeGenericProgress` to supply `boundary_anchor_source`. Assert the diagnostic
callback contains `boundary_anchor_source`, `TRACE_FIELDS` contains the column after
`boundary_confirmed`, and `summarize_trace()` returns:

```python
"boundary_anchor_source_counts": {
    "boundary_anchor_exact": 1,
    "boundary_anchor_interpolated": 1,
    "boundary_anchor_nearest": 1,
    "boundary_anchor_missing": 1,
}
```

Only count non-empty values on confirmed boundary rows.

- [ ] **Step 7: Run diagnostic tests and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_application_pipeline tests.test_progress_diagnostic_cli -v
```

Expected: FAIL because pipeline diagnostics and trace summaries do not expose anchor
provenance.

- [ ] **Step 8: Implement diagnostic-only provenance propagation**

Add this field to `_report_generic_progress()`:

```python
"boundary_anchor_source": (
    None
    if frame_result.boundary_anchor_source is None
    else frame_result.boundary_anchor_source.value
),
```

Add `boundary_anchor_source` to `TRACE_FIELDS`. In `summarize_trace()`, count non-empty
anchor sources only where `boundary_confirmed` is truthy. Do not add this field to the
legacy production record dictionary or normalized telemetry contract.

- [ ] **Step 9: Run focused/full verification and commit integration**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_progress_fusion tests.test_application_pipeline tests.test_progress_diagnostic_cli -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
PYTHONPATH=src .venv/bin/python -m compileall -q src scripts tests main.py run_server.py
git diff --check
```

Expected: focused and full suites pass, compilation is silent, and the legacy record
schema remains unchanged.

Commit:

```bash
git add src/acc_telemetry/application/progress.py src/acc_telemetry/application/pipeline.py scripts/diagnose_progress.py tests/test_progress_fusion.py tests/test_application_pipeline.py tests/test_progress_diagnostic_cli.py
git commit -m "feat: integrate confirmed boundary anchor recovery"
```

### Task 4: Validate all three captures and record the gate

**Files:**
- Modify: `docs/current-status.md`
- Modify: `docs/acc-ps5-plan.md` only if the `s` stage gate changes
- Modify: `docs/superpowers/plans/2026-09-05-generic-boundary-visual-anchor.md`
- Local ignored output: `data/lab/2026-09-05-boundary-visual-anchor/`

- [ ] **Step 1: Verify immutable inputs and ignored output before replay**

Run:

```bash
stat -f '%z %N' '/Users/loiclang/Movies/2026-09-03 22-42-08.mov' data/lab/2026-09-03-generic-s-fusion/clean-bmw-representative.mov data/lab/2026-09-03-generic-s-fusion/crash-representative.mov
git check-ignore data/lab/2026-09-05-boundary-visual-anchor/new-bmw/trace.csv
```

Expected sizes before replay:

```text
1119948389 /Users/loiclang/Movies/2026-09-03 22-42-08.mov
367156505 data/lab/2026-09-03-generic-s-fusion/clean-bmw-representative.mov
453613415 data/lab/2026-09-03-generic-s-fusion/crash-representative.mov
```

The ignored-output check must print the requested trace path.

- [ ] **Step 2: Run the new BMW replay first**

```bash
PYTHONPATH=src .venv/bin/python scripts/diagnose_progress.py '/Users/loiclang/Movies/2026-09-03 22-42-08.mov' --profile ps5_full_map_1080p --output-dir data/lab/2026-09-05-boundary-visual-anchor/new-bmw
```

Require:

- exactly four confirmed boundaries and three accepted calibration laps;
- effective length remains close to the prior measured `6962.810 m` and no accepted
  lap becomes an outlier solely because of this change;
- first boundary source is exact or interpolated, not missing;
- the following complete lap contains fused visual progress rather than remaining
  unavailable through the next boundary;
- zero unconfirmed resets, nonlocal visual jumps, and premature completions;
- no circuit-specific rule was introduced to achieve the result.

If this fails, stop. Convert the smallest numeric failure into a synthetic RED test in
the owning task before changing production code.

- [ ] **Step 3: Run both representative controls**

```bash
PYTHONPATH=src .venv/bin/python scripts/diagnose_progress.py data/lab/2026-09-03-generic-s-fusion/clean-bmw-representative.mov --profile ps5_full_map_1080p --output-dir data/lab/2026-09-05-boundary-visual-anchor/clean-control
PYTHONPATH=src .venv/bin/python scripts/diagnose_progress.py data/lab/2026-09-03-generic-s-fusion/crash-representative.mov --profile ps5_full_map_1080p --output-dir data/lab/2026-09-05-boundary-visual-anchor/crash-control
```

Require clean control:

- three confirmed boundaries and two accepted calibration laps;
- maximum checkpoint spread remains `<= 0.002`;
- zero resets, jumps, or premature completions.

Require crash control:

- four confirmed boundaries;
- lap 6 remains rejected with `duration_outlier`;
- effective calibration remains based on two accepted regular laps near `6960.709 m`;
- zero resets, jumps, or premature completions;
- missing/degraded evidence remains explicit rather than forced observed.

- [ ] **Step 4: Inspect anchor provenance and update durable status**

Read the three `summary.json` files and boundary rows in their traces. Record in
`docs/current-status.md`:

- source counts and boundary-anchor source counts;
- effective length, rejected laps, checkpoint spread, and unavailable duration;
- whether the first complete BMW lap is recovered;
- zero/non-zero safety metrics;
- exact next action.

If all gates pass, update `docs/acc-ps5-plan.md` to mark this isolated anchor gap
resolved while keeping the historical 2026-09-01 confirmer replay and remaining
field-quality gates ahead of corner analysis. Check off this plan only for work
actually completed.

- [ ] **Step 5: Run final verification**

```bash
./scripts/docs-list
PYTHONPATH=src .venv/bin/python -m compileall -q src scripts tests main.py run_server.py
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
rg -n -i 'spa|francorchamps|la source|raidillon|les combes|bruxelles|359, 0|70, 155' src tests config
git status --short --branch
```

Expected: documentation discovery succeeds, compilation is silent, all tests pass,
and the circuit search finds no new production or test rule. Documentation may retain
Spa evidence. The worktree contains only the intended documentation changes.

- [ ] **Step 6: Commit verified replay evidence without local artifacts**

Inspect the staged diff before committing:

```bash
git add docs/current-status.md docs/superpowers/plans/2026-09-05-generic-boundary-visual-anchor.md
git add docs/acc-ps5-plan.md  # only when the stage-gate text changed
git diff --cached --check
git diff --cached --stat
git diff --cached
git commit -m "docs: validate generic boundary anchor recovery"
```

Do not stage anything under `data/lab/`. Do not merge or push. Report the branch,
commits, replay metrics, and remaining reliability gates for user review.

## Final measurable acceptance checklist

- A compact 16 by 16 irregular contour with measured sub-0.35 circularity is retained
  through dimensionless shape evidence.
- Elongated, sparse, tiny, oversized, and zero-moment red regions remain rejected.
- Projection and temporal scoring, not extraction, choose the visual truth.
- Exact boundary projection always takes precedence.
- Bracketing interpolation is odometry-weighted and handles wrapped `0.998 -> 0.002`.
- One-sided recovery passes stricter time and normalized-distance gates and exposes
  higher uncertainty.
- Ambiguous, distant, or cross-boundary evidence produces `boundary_anchor_missing`.
- No raw OCR value or visual observation can create or reset a lap.
- The new BMW first complete lap becomes visually fused without safety regressions.
- The clean control retains spread `<= 0.002`.
- The crash control retains rejected-lap calibration and explicit degradation.
- Focused tests, full suite, compilation, docs discovery, and diff checks pass.
- No source video or ignored diagnostic artifact is modified or committed.

## Intended atomic commit sequence

1. `fix: retain compact red map candidates`
2. `feat: recover bounded boundary visual anchors`
3. `feat: integrate confirmed boundary anchor recovery`
4. `docs: validate generic boundary anchor recovery`
