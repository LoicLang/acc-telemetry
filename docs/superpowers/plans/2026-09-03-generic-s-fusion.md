---
summary: detailed TDD execution plan for circuit-generic odometric, visual, and fused longitudinal progress
read_when:
  - implementing the approved generic fused s milestone
  - changing speed integration, red-dot candidates, centerline topology, lap anchoring, or progress quality
---

# Generic `s` Fusion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the legacy map-only `track_position` behavior with a circuit-generic, explainable `s_fused` built from independent speed odometry and visual-map evidence, anchored only by confirmed lap transitions.

**Architecture:** OpenCV-bound extraction will emit every plausible red-dot candidate and one validated centerline; pure application code will integrate speed, confirm lap boundaries, project candidates with temporal context, calibrate effective lap length, and fuse the signals. The normalization/domain boundary will expose `s_odometry`, `s_visual`, `s_fused`, source, uncertainty, and reasons while a tested adapter keeps the legacy `track_position` percentage readable during migration.

**Tech Stack:** Python 3.13, NumPy, OpenCV, dataclasses, `unittest`, CSV/JSON diagnostics, Git

---

## Constraints and stage gates

- Treat `/Users/loiclang/Movies/2026-09-02 21-55-05.mov` and `/Users/loiclang/Movies/2026-09-02 22-40-01.mov` as immutable inputs. Never copy them into Git, rewrite them, or write beside them.
- Write all real-session outputs below ignored `data/lab/2026-09-03-generic-s-fusion/`.
- No string, coordinate, map image, corner name, or threshold keyed to Spa may enter production code or tracked tests. Synthetic tests use generic loops and neutral names.
- Do not use official circuit length as the denominator. Learn `effective_lap_length_m` only from complete, accepted boundary-to-boundary laps.
- Do not reset or anchor progress from map geometry or an unconfirmed OCR change.
- Do not remove legacy smoothing or forced-completion code until the fused estimator passes its focused tests and both replay gates. There is no silent fallback from failed fusion to the legacy saturated value.
- After every RED test, confirm the failure is caused by missing intended behavior. After every GREEN step, run the focused module and the full suite before committing.

## Planned file structure

| File | Responsibility |
| --- | --- |
| `src/acc_telemetry/domain/progress.py` | Extraction-independent progress values, sources, reasons, and uncertainty contract. |
| `src/acc_telemetry/extraction/map_progress.py` | Red candidate extraction, centerline thinning/topology validation, and geometric projection. This is the only new module allowed to import OpenCV. |
| `src/acc_telemetry/application/odometry.py` | Timestamp-aware `v * dt` integration, gap policy, lap-distance summaries, and robust effective-length calibration. |
| `src/acc_telemetry/application/lap_state.py` | Raw lap observations and confirmed transition state machine. |
| `src/acc_telemetry/application/progress.py` | Odometry-guided visual selection, fusion state, trusted anchoring, and offline replay. |
| `src/acc_telemetry/application/pipeline.py` | Collect raw frame observations, run the offline progress replay, and attach compatible output fields. |
| `src/acc_telemetry/application/components.py` | Construct the generic centerline/fusion components from validated settings. |
| `src/acc_telemetry/application/config.py` and `config/telemetry.yaml` | Validated, circuit-independent odometry, topology, projection, fusion, and confirmation thresholds. |
| `src/acc_telemetry/domain/telemetry.py` and `src/acc_telemetry/normalization/samples.py` | Carry fused progress and field-level provenance into `TelemetrySample`. |
| `scripts/diagnose_progress.py` | Generate ignored per-frame traces and measured validation summaries for local captures. |
| `tests/test_odometry.py` | Synthetic integration, gap, calibration, and uncertainty tests. |
| `tests/test_map_progress.py` | Synthetic images/masks for all-candidate extraction and unique-centerline topology. |
| `tests/test_lap_state.py` | Raw-versus-confirmed lap transition tests. |
| `tests/test_progress_fusion.py` | Temporal projection, anchoring, fusion, gaps, ambiguity, and crash-lap rejection. |
| `tests/test_application_pipeline.py` | Two-pass orchestration and legacy compatibility tests. |
| `tests/test_normalization.py` | Domain propagation and source/quality compatibility tests. |
| `tests/test_progress_diagnostic_cli.py` | Stable diagnostic schema and validation-metric tests. |

## Public contracts fixed by this plan

Create these names once in Task 1 and reuse them unchanged:

```python
class ProgressSource(StrEnum):
    OBSERVED = "observed"
    FUSED = "fused"
    PREDICTED = "predicted"
    INTERPOLATED = "interpolated"
    MISSING = "missing"


@dataclass(frozen=True)
class ProgressEstimate:
    s_fused: float | None
    s_odometry: float | None
    s_visual: float | None
    distance_m: float
    effective_lap_length_m: float | None
    uncertainty: float
    source: ProgressSource
    reasons: tuple[str, ...]
    anchored: bool


@dataclass(frozen=True)
class RedDotCandidate:
    centroid: tuple[float, float]
    area_px: float
    area_fraction: float
    circularity: float


@dataclass(frozen=True)
class Centerline:
    points: tuple[tuple[float, float], ...]
    cumulative_length_px: tuple[float, ...]
    total_length_px: float


@dataclass(frozen=True)
class LapObservation:
    frame: int
    time_s: float
    raw_lap_number: int | None


@dataclass(frozen=True)
class ConfirmedLapBoundary:
    frame: int
    time_s: float
    from_lap: int
    to_lap: int
    confidence: float
```

All normalized `s` values and uncertainty values use `[0, 1]`. Wrapped deltas use the closed interval convention `(-0.5, 0.5]`. Reasons are stable snake-case values suitable for CSV and tests, including `unanchored`, `speed_missing`, `speed_anomalous`, `speed_gap_interpolated`, `visual_missing`, `visual_ambiguous`, `visual_out_of_gate`, `lap_boundary_confirmed`, `uncertainty_limit`, and `calibration_lap_rejected`.

### Task 1: Establish the `s_odometry` contract and its validated generic settings

**Files:**
- Create: `src/acc_telemetry/domain/progress.py`
- Modify: `src/acc_telemetry/domain/__init__.py`
- Modify: `src/acc_telemetry/application/config.py`
- Modify: `config/telemetry.yaml`
- Modify: `tests/test_configuration.py`
- Create: `tests/test_progress_contract.py`

- [x] **Step 1: Write failing contract and settings tests**

Add tests that instantiate the exact dataclasses above, reject `ProgressEstimate` values outside `[0, 1]`, and assert these settings load:

```yaml
progress:
  odometry:
    max_interpolation_gap_s: 0.25
    observed_uncertainty_per_s: 0.00005
    interpolated_uncertainty_per_s: 0.001
  candidates:
    min_area_fraction: 0.00002
    max_area_fraction: 0.005
    min_circularity: 0.35
  centerline:
    max_branch_length_fraction: 0.03
    min_cycle_diagonal_fraction: 2.0
    resample_spacing_diagonal_fraction: 0.0025
  projection:
    max_centerline_distance_diagonal_fraction: 0.03
    max_progress_error: 0.04
    min_score_margin: 0.15
  fusion:
    visual_gain: 0.35
    short_visual_gap_s: 0.5
    unavailable_uncertainty: 0.05
  lap_confirmation:
    consecutive_observations: 5
  calibration:
    max_missing_speed_fraction: 0.01
    max_relative_mad: 0.03
```

Test that zero/negative durations, fractions outside `[0, 1]`, `min_area_fraction >= max_area_fraction`, and `visual_gain > 1` raise `ConfigurationError` naming the exact key.

- [x] **Step 2: Run the tests and confirm RED**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_progress_contract tests.test_configuration -v
```

Expected: FAIL because `acc_telemetry.domain.progress` and `TelemetrySettings.progress` do not exist.

- [x] **Step 3: Add the immutable contracts and nested validated settings**

Implement `ProgressEstimate.__post_init__` with explicit range checks:

```python
def __post_init__(self) -> None:
    for name in ("s_fused", "s_odometry", "s_visual"):
        value = getattr(self, name)
        if value is not None and not 0.0 <= value <= 1.0:
            raise ValueError(f"{name} must be in [0, 1]")
    if not 0.0 <= self.uncertainty <= 1.0:
        raise ValueError("uncertainty must be in [0, 1]")
    if self.anchored is False and self.s_fused is not None:
        raise ValueError("unanchored progress cannot expose s_fused")
```

Represent each settings group as a frozen dataclass. Extend `load_settings()` with `_fraction()` and `_positive()` helpers so every threshold is validated centrally. Export only domain types from `domain/__init__.py`; do not import application or OpenCV code there.

- [x] **Step 4: Run focused and full tests and confirm GREEN**

Run:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_progress_contract tests.test_configuration -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Expected: all tests pass and existing 720p/1080p settings still load.

- [x] **Step 5: Commit the contract**

```bash
git add config/telemetry.yaml src/acc_telemetry/domain/progress.py src/acc_telemetry/domain/__init__.py src/acc_telemetry/application/config.py tests/test_progress_contract.py tests/test_configuration.py
git commit -m "feat: define odometric progress contracts"
```

### Task 2: Build the independent `s_odometry` baseline first

**Files:**
- Create: `src/acc_telemetry/application/odometry.py`
- Create: `tests/test_odometry.py`

- [x] **Step 1: Write failing integration tests**

Cover these exact cases with synthetic observations:

```python
def test_integrates_constant_speed_with_trapezoidal_intervals():
    samples = [
        SpeedObservation(0.0, 72.0, QualityFlag.OBSERVED),
        SpeedObservation(5.0, 72.0, QualityFlag.OBSERVED),
        SpeedObservation(10.0, 72.0, QualityFlag.OBSERVED),
    ]
    trace = integrate_speed(samples, max_interpolation_gap_s=0.25)
    assert trace[-1].distance_m == 200.0
    assert trace[-1].source is ProgressSource.OBSERVED


def test_never_integrates_negative_or_duplicate_time():
    samples = [
        SpeedObservation(1.0, 36.0, QualityFlag.OBSERVED),
        SpeedObservation(1.0, 36.0, QualityFlag.OBSERVED),
        SpeedObservation(0.9, 36.0, QualityFlag.OBSERVED),
    ]
    trace = integrate_speed(samples, max_interpolation_gap_s=0.25)
    assert trace[-1].distance_m == 0.0
    assert "non_monotonic_time" in trace[-1].reasons
```

Also assert: km/h is divided by 3.6; observed endpoints use trapezoidal integration; a missing speed across `0.2 s` is linearly interpolated and increases uncertainty; a missing speed across `0.3 s` adds no claimed distance and produces `MISSING`; anomalous speed is never treated as observed; uncertainty is monotonic during missing intervals.

- [x] **Step 2: Run the test and confirm RED**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_odometry -v
```

Expected: FAIL because `SpeedObservation`, `OdometryPoint`, and `integrate_speed()` do not exist.

- [x] **Step 3: Implement minimal timestamp-aware integration**

Use immutable inputs and outputs:

```python
@dataclass(frozen=True)
class SpeedObservation:
    time_s: float
    speed_kmh: float | None
    quality: QualityFlag


@dataclass(frozen=True)
class OdometryPoint:
    time_s: float
    distance_m: float
    delta_distance_m: float | None
    uncertainty: float
    source: ProgressSource
    reasons: tuple[str, ...]
```

For each strictly positive `dt`, integrate `((v0 + v1) / 2) / 3.6 * dt` only when both endpoints are observed, or when a bounded internal gap can be explicitly interpolated. Keep distance unchanged for unavailable intervals; do not replace missing distance with zero-quality movement. Clamp uncertainty to `1.0`, not the signal.

- [x] **Step 4: Add RED/GREEN calibration tests**

Define complete laps only from pairs of `ConfirmedLapBoundary`. Test distances `[7000, 7010, 6990, 9100]`: the first three yield `effective_lap_length_m == 7000`, while the 9100 m crash/off-track outlier is rejected and reports `calibration_lap_rejected`. Reject laps with an unbounded speed gap, missing boundary, non-positive distance, or missing-speed fraction above configuration. A single accepted lap may normalize itself offline but must report higher calibration uncertainty; three accepted laps use the median and median absolute deviation.

Run the test before and after implementing `summarize_lap_distances()` and `calibrate_effective_lap_length()`:

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_odometry -v
```

Expected RED: calibration symbols missing. Expected GREEN: exact integration and outlier-rejection assertions pass.

- [x] **Step 5: Run full tests and commit**

```bash
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git add src/acc_telemetry/application/odometry.py tests/test_odometry.py
git commit -m "feat: integrate speed into odometric progress"
```

### Task 3: Extract every plausible red candidate

**Files:**
- Create: `src/acc_telemetry/extraction/map_progress.py`
- Create: `tests/test_map_progress.py`
- Modify: `src/acc_telemetry/extraction/__init__.py`

- [x] **Step 1: Write the failing all-candidate tests**

Build BGR arrays in memory. One image contains a 31x31 red background region and two circular red candidates inside the configured fractional area/circularity limits. Assert that the large region is rejected individually and both plausible candidates remain, sorted deterministically by `(centroid_y, centroid_x)`. Add cases for empty input, zero-moment contours, a tiny speck, an elongated red bar, and both HSV red ranges.

```python
candidates = extract_red_candidates(
    image,
    min_area_fraction=0.00002,
    max_area_fraction=0.005,
    min_circularity=0.35,
)
self.assertEqual([candidate.centroid for candidate in candidates], [(70.0, 30.0), (72.0, 70.0)])
self.assertTrue(all(candidate.area_fraction < 0.005 for candidate in candidates))
```

- [x] **Step 2: Run and confirm RED**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_map_progress -v
```

Expected: FAIL because `extract_red_candidates()` is missing.

- [x] **Step 3: Implement candidate extraction without selecting truth**

Use the existing dual HSV masks, `cv2.RETR_EXTERNAL`, and calculate `area_fraction = contour_area / (height * width)` and `circularity = 4 * pi * area / perimeter**2`. Filter each contour independently, calculate its floating-point centroid, and return all survivors. Do not use `max(contours, ...)`, previous progress, or Spa geometry in this function.

- [x] **Step 4: Confirm GREEN, preserve characterization, and commit**

Update `tests/test_position_tracker_v2.py::test_characterizes_large_red_background_masking_valid_dot` only after the new test is green: keep it as a legacy characterization and assert the new function returns the valid smaller candidate. Do not change `PositionTrackerV2.detect_red_dot()` yet.

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_map_progress tests.test_position_tracker_v2 -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git add src/acc_telemetry/extraction/map_progress.py src/acc_telemetry/extraction/__init__.py tests/test_map_progress.py tests/test_position_tracker_v2.py
git commit -m "feat: retain plausible red map candidates"
```

### Task 4: Derive one generic validated centerline

**Files:**
- Modify: `src/acc_telemetry/extraction/map_progress.py`
- Modify: `tests/test_map_progress.py`

- [x] **Step 1: Write failing topology and resampling tests**

Generate masks for: a thick rectangular ring; the same ring with a short start-marker spur; an open curve; two disjoint rings; a ring with a branch longer than the configured fraction; and a tiny ring. Assert the accepted ring yields a one-pixel ordered closed cycle, every graph node has degree two after pruning, cumulative lengths strictly increase, the closing edge is included, and resampling has stable spacing within one source pixel.

Assert exact error reasons through `CenterlineTopologyError.reason`: `no_closed_cycle`, `multiple_cycles`, `excessive_branches`, `discontinuous_path`, and `implausibly_short_path`. There must be no fallback result.

- [x] **Step 2: Run and confirm RED**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_map_progress.TestCenterline -v
```

Expected: FAIL because `build_centerline()` and `CenterlineTopologyError` are absent.

- [x] **Step 3: Implement mask reduction and explicit topology validation**

Implement these private stages in order, each covered directly through public behavior:

```python
def build_centerline(
    white_probability: np.ndarray,
    *,
    frequency_threshold: float,
    max_branch_length_fraction: float,
    min_cycle_diagonal_fraction: float,
    resample_spacing_diagonal_fraction: float,
) -> Centerline:
    binary = threshold_probability(white_probability, frequency_threshold)
    component = largest_connected_component(binary)
    skeleton = morphological_skeleton(component)
    graph = pixel_graph(skeleton)
    graph = prune_short_terminal_branches(graph, max_branch_length_fraction)
    cycle = require_single_closed_cycle(graph, min_cycle_diagonal_fraction)
    ordered = order_cycle(cycle)
    return resample_closed_path(ordered, resample_spacing_diagonal_fraction)
```

Use 8-neighbour pixel adjacency and scale branch/cycle/resampling limits by ROI diagonal or extracted cycle length, never by a circuit name or absolute Spa coordinate. Preserve the white-frequency construction currently used by `PositionTrackerV2`, but move the new centerline path into this focused module. Do not call `_detect_start_finish_line()`.

- [x] **Step 4: Add a regression for parallel contour ambiguity**

Use the synthetic two-pixel-thick return path from the existing characterization. Assert projections onto the new ordered centerline differ locally rather than jumping by more than `0.4` normalized progress. Keep the old tracker characterization unchanged until migration.

- [x] **Step 5: Run focused/full tests and commit**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_map_progress tests.test_position_tracker_v2 -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git add src/acc_telemetry/extraction/map_progress.py tests/test_map_progress.py
git commit -m "feat: build validated generic map centerline"
```

Stop the milestone here if the real Spa mask cannot produce one cycle without track-specific logic. Record `no_closed_cycle`, `multiple_cycles`, or `excessive_branches` and compare the two alternatives from the approved specification before adding another heuristic.

### Task 5: Project visual candidates using odometric temporal context

**Files:**
- Modify: `src/acc_telemetry/extraction/map_progress.py`
- Create: `src/acc_telemetry/application/progress.py`
- Create: `tests/test_progress_fusion.py`
- Modify: `tests/test_map_progress.py`

- [x] **Step 1: Write failing geometric projection tests**

Make `project_candidate(candidate, centerline)` return every segment projection within the configured distance gate as `VisualProjection(s_visual, distance_px, projected_xy)`. Test wraparound at `0/1`, interpolation between resampled points, and multiple projections for visually close centerline branches. Geometry must not choose the winning branch.

- [x] **Step 2: Run and confirm RED, then implement the geometric projection**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_map_progress.TestProjection -v
```

Expected RED: projection API missing. Implement orthogonal point-to-segment projection and normalized arc length, rerun, and expect GREEN.

- [x] **Step 3: Write failing temporal-selection tests**

Define:

```python
@dataclass(frozen=True)
class VisualSelection:
    s_visual: float | None
    centroid: tuple[float, float] | None
    score: float | None
    uncertainty: float
    source: ProgressSource
    reasons: tuple[str, ...]
```

Test the measured failure shape generically: two spatially adjacent branches project to `0.015` and `0.347`, while odometry predicts `0.018`; select `0.015`. Test that 2D displacement, wrapped progress error, projection distance, elapsed time, speed-derived maximum movement, and current uncertainty all contribute. If the top two normalized scores differ by less than `min_score_margin`, return `s_visual=None` with `visual_ambiguous`. If every candidate violates the physical/projection gate, return `visual_out_of_gate`. With no candidates, return `visual_missing`.

- [x] **Step 4: Implement deterministic scoring**

Implement `select_visual_projection()` with a documented lower-is-better score whose terms are normalized by configured gates:

```text
score = 0.40 * progress_error / progress_gate
      + 0.30 * centerline_distance / distance_gate
      + 0.30 * image_displacement / displacement_gate
```

Expand `progress_gate` by current odometric uncertainty. Derive `displacement_gate` from `speed_kmh * dt` only as a consistency bound; because pixels/metre is unknown, combine it with prior accepted image displacement and ROI diagonal. Do not convert map pixels to physical metres. Break exact-score ties only by stable candidate/projection ordering, then still reject them as ambiguous because their margin is zero.

- [x] **Step 5: Run focused/full tests and commit**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_map_progress tests.test_progress_fusion -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git add src/acc_telemetry/extraction/map_progress.py src/acc_telemetry/application/progress.py tests/test_map_progress.py tests/test_progress_fusion.py
git commit -m "feat: guide visual projection with odometry"
```

### Task 6: Confirm lap transitions before any anchor or reset

**Files:**
- Create: `src/acc_telemetry/application/lap_state.py`
- Create: `tests/test_lap_state.py`
- Modify: `src/acc_telemetry/application/components.py`
- Modify: `tests/test_configuration.py`

- [x] **Step 1: Write failing raw-versus-confirmed state tests**

Test these sequences with `consecutive_observations=5`:

- `[8, 8, 9, 8, 8]` produces no boundary;
- `[8, 8, 9, 9, 9, 9, 9]` produces exactly one `8 -> 9` boundary on the fifth stable 9;
- missing values retain confirmed lap 8 without creating observations;
- `8 -> 10`, `8 -> 7`, and a stale repeated 9 after confirmation produce no boundary;
- the boundary confidence is `stable_count / required_count`, capped at 1.0;
- raw values remain inspectable even when rejected.

- [x] **Step 2: Run and confirm RED**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_lap_state -v
```

Expected: FAIL because `LapTransitionConfirmer` is missing.

- [x] **Step 3: Implement a pure confirmation state machine**

`LapTransitionConfirmer.observe(LapObservation)` returns a state containing `raw_lap_number`, `confirmed_lap_number`, optional `ConfirmedLapBoundary`, confidence, and reasons. Only `confirmed + 1` may become pending; any return to the confirmed number clears pending evidence. Initialization requires the same stable consensus but emits no boundary because there is no known preceding lap.

- [x] **Step 4: Wire configuration without changing the pipeline yet**

Make `ProcessingComponents` carry a configured confirmer factory or instance. Assert the factory receives `settings.progress.lap_confirmation.consecutive_observations`. Do not call legacy `detect_lap_transition()` from the new component.

- [x] **Step 5: Run focused/full tests and commit**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_lap_state tests.test_configuration -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git add src/acc_telemetry/application/lap_state.py src/acc_telemetry/application/components.py tests/test_lap_state.py tests/test_configuration.py
git commit -m "feat: confirm trusted lap boundaries"
```

### Task 7: Fuse odometry and visual evidence with explicit uncertainty

**Files:**
- Modify: `src/acc_telemetry/application/progress.py`
- Modify: `tests/test_progress_fusion.py`

- [x] **Step 1: Write failing anchor and fusion tests**

Use a 1000 m effective lap length and synthetic boundaries. Assert:

- before the first confirmed boundary, `s_fused is None`, `anchored is False`, and reason is `unanchored`, even if visual candidates exist;
- a confirmed boundary yields exactly `s_fused == 0.0` and `lap_boundary_confirmed`;
- 100 m of observed odometry predicts `s_odometry == 0.1`;
- reliable `s_visual == 0.11` corrects with `visual_gain=0.35` to `s_fused == 0.1035`, using wrapped deltas;
- a short visual gap emits `PREDICTED` with increasing uncertainty;
- an explicitly bounded speed gap emits `INTERPOLATED`;
- after `uncertainty >= unavailable_uncertainty`, `s_fused is None` with `uncertainty_limit` rather than held progress;
- no raw OCR change, visual wrap, geometric point, or `s_visual` near zero resets the lap;
- progress cannot enter the completion band before a confirmed next boundary unless odometry genuinely predicts it; no forced `1.0` exists.

- [x] **Step 2: Run and confirm RED**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_progress_fusion.TestFusedEstimator -v
```

Expected: FAIL because `FusedProgressEstimator` is missing.

- [x] **Step 3: Implement the minimal state update**

Use odometry for prediction and visual evidence only as a correction:

```python
predicted = wrap01(previous_s + delta_distance_m / effective_lap_length_m)
if selection.s_visual is not None:
    correction = wrapped_delta(selection.s_visual, predicted)
    fused = wrap01(predicted + visual_gain * correction)
    source = ProgressSource.FUSED
else:
    fused = predicted
    source = odometry_source
```

Reduce uncertainty only when visual selection is unambiguous; otherwise add odometry and gap uncertainty. A confirmed boundary resets cumulative lap distance and the wrapped coordinate but retains a session-total distance for diagnostics. Return a fresh immutable `ProgressEstimate` every frame.

- [x] **Step 4: Write and pass offline rebasing/calibration tests**

Implement `estimate_progress(observations, centerline, settings)`. It must first derive confirmed boundaries and odometric lap summaries, calibrate from accepted complete laps, then replay frames. A partial opening lap stays unanchored. A captured lap bounded on both sides may be rebased offline. Crash/outlier laps can receive estimates but never update `effective_lap_length_m`.

- [x] **Step 5: Run focused/full tests and commit**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_odometry tests.test_lap_state tests.test_progress_fusion -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git add src/acc_telemetry/application/progress.py tests/test_progress_fusion.py
git commit -m "feat: fuse progress with uncertainty and trusted anchors"
```

### Task 8: Propagate fused progress through the pipeline and domain

**Files:**
- Modify: `src/acc_telemetry/application/pipeline.py`
- Modify: `src/acc_telemetry/application/components.py`
- Modify: `src/acc_telemetry/domain/telemetry.py`
- Modify: `src/acc_telemetry/normalization/samples.py`
- Modify: `tests/test_application_pipeline.py`
- Modify: `tests/test_normalization.py`

- [x] **Step 1: Write failing two-pass pipeline tests**

Extend fakes to yield at least two confirmed boundaries and candidate lists. Assert the pipeline collects raw frame observations first and calls `estimate_progress()` only after extraction. Assert every record receives:

```python
{
    "track_position": 10.35,
    "s_odometry": 0.10,
    "s_visual": 0.11,
    "s_fused": 0.1035,
    "s_uncertainty": 0.002,
    "s_source": "fused",
    "s_reasons": "visual_correction",
}
```

`track_position` must equal `s_fused * 100` only when fused progress is available; otherwise it is `None`. Assert `position_diagnostic_callback` exposes the new fields and never reports a legacy held/saturated value as fused output.

- [x] **Step 2: Run and confirm RED**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_application_pipeline -v
```

Expected: FAIL because the pipeline still invokes `PositionTrackerV2.extract_position()` frame by frame.

- [x] **Step 3: Implement raw collection and offline replay**

During the frame loop, collect timestamp, speed plus quality, raw lap observation, confirmed lap state, and `extract_red_candidates()` output. After the loop, call the estimator and merge one estimate into each matching record. Preserve controls, gear, lap time, video closing, progress callbacks, and existing profiles. Keep legacy `PositionTrackerV2` importable but stop constructing or invoking it in the production component path once the new path passes focused tests.

- [x] **Step 4: Write failing normalization/domain tests**

Extend `TelemetrySample` with optional `s_odometry`, `s_visual`, `s_uncertainty`, `s_source`, and `s_reasons`. Add `PREDICTED` and `FUSED` to `QualityFlag`. Assert `normalize_row()` prefers `s_fused`, parses numeric optional fields, maps `s_source` to `field_quality["s"]`, preserves reasons as anomalies/evidence without flattening them, and continues accepting old rows containing only `track_position`.

- [x] **Step 5: Implement normalization and confirm compatibility**

Old rows retain current semantics. New rows satisfy:

```python
sample.s == row["s_fused"]
sample.field_quality["s"] == QualityFlag(row["s_source"])
sample.source_values["track_position"] == row["track_position"]
```

Treat `missing` as `s=None`; never promote `predicted`, `interpolated`, or `fused` to `observed`.

- [x] **Step 6: Run focused/full tests and commit**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_application_pipeline tests.test_normalization tests.test_web_profile_selection -v
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git add src/acc_telemetry/application/pipeline.py src/acc_telemetry/application/components.py src/acc_telemetry/domain/telemetry.py src/acc_telemetry/normalization/samples.py tests/test_application_pipeline.py tests/test_normalization.py
git commit -m "feat: propagate fused progress through telemetry"
```

### Task 9: Add reproducible clean-session validation

**Files:**
- Create: `scripts/diagnose_progress.py`
- Create: `tests/test_progress_diagnostic_cli.py`
- Modify: `docs/current-status.md`

- [x] **Step 1: Write failing diagnostic schema and metric tests**

Define stable per-frame fields: frame, time, raw/confirmed lap, boundary confidence, candidate count, selected centroid, `s_odometry`, `s_visual`, `s_fused`, distance, effective lap length, uncertainty, source, reasons, and anchored. Define summary JSON fields: input path, file size, profile, frame count, confirmed boundary count, calibration lap count, rejected calibration laps, premature completion count, unconfirmed reset count, nonlocal visual jump count, comparable-checkpoint spread, source counts, unavailable duration, and pass/fail criteria.

Unit-test metric functions with small rows. In particular, `premature_completion_count` counts entries into `s_fused >= 0.999` before a boundary, `unconfirmed_reset_count` counts wrapped resets without a boundary, and checkpoint spread uses the same odometric distance bins across accepted repeated laps.

- [x] **Step 2: Run and confirm RED, then implement the CLI**

```bash
PYTHONPATH=src .venv/bin/python -m unittest tests.test_progress_diagnostic_cli -v
```

Expected RED: module missing. Implement `write_trace()`, `summarize_trace()`, and argument validation. The CLI must refuse an output path equal to either input video path.

- [x] **Step 3: Run unit/full verification before touching real evidence**

```bash
./scripts/docs-list
PYTHONPATH=src .venv/bin/python -m compileall -q src scripts tests main.py run_server.py
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
```

Expected: documentation discovery succeeds, compilation is silent, and all tests pass.

- [x] **Step 4: Replay the clean BMW session into ignored output**

First re-check size and existence, then run:

```bash
stat -f '%z %N' '/Users/loiclang/Movies/2026-09-02 21-55-05.mov'
PYTHONPATH=src .venv/bin/python scripts/diagnose_progress.py '/Users/loiclang/Movies/2026-09-02 21-55-05.mov' --profile ps5_full_map_1080p --output-dir data/lab/2026-09-03-generic-s-fusion/clean-bmw
```

Required clean-session exit criteria:

- at least two complete accepted laps and at least three confirmed boundaries;
- zero resets without `ConfirmedLapBoundary`;
- zero forced-completion decisions and zero entries into `s_fused >= 0.999` before the next confirmed boundary;
- zero accepted frame-to-frame visual jumps greater than `0.10` normalized progress unless a confirmed boundary occurred;
- repeated checkpoint spread at each reported bin is no worse than `0.002` (0.2 percentage point), with the number of laps and bins reported;
- short visual gaps are labelled predicted/interpolated, and any uncertainty-limit interval is unavailable rather than observed;
- effective lap length is derived from accepted complete laps and each rejected lap names its reason.

If a criterion fails, do not tune against Spa coordinates. Add a minimal generic synthetic RED regression reproducing the failure, implement the generic correction in the owning task’s module, rerun focused/full tests, and create a separate atomic fix commit.

- [x] **Step 5: Record only durable summary evidence and commit**

Update `docs/current-status.md` with command, input size, summary metrics, exact pass/fail gates, and the next action. Do not commit trace CSV, JSON output, frames, screenshots, or video.

```bash
git check-ignore data/lab/2026-09-03-generic-s-fusion/clean-bmw/trace.csv
git status --short
git add scripts/diagnose_progress.py tests/test_progress_diagnostic_cli.py docs/current-status.md
git commit -m "test: validate fused progress on clean laps"
```

### Task 10: Prove robustness on the crash-heavy secondary session

**Files:**
- Modify: `tests/test_progress_fusion.py`
- Modify: `tests/test_progress_diagnostic_cli.py`
- Modify: `docs/current-status.md`
- Modify: `docs/acc-ps5-plan.md` only if a reliability stage gate changes
- Modify: `docs/architecture.md` when the production data flow has actually migrated
- Modify: `README.md` when the user-visible diagnostic command is stable

- [x] **Step 1: Run the secondary replay without changing code**

```bash
stat -f '%z %N' '/Users/loiclang/Movies/2026-09-02 22-40-01.mov'
PYTHONPATH=src .venv/bin/python scripts/diagnose_progress.py '/Users/loiclang/Movies/2026-09-02 22-40-01.mov' --profile ps5_full_map_1080p --output-dir data/lab/2026-09-03-generic-s-fusion/crash-heavy
```

Required robustness criteria:

- zero resets without a confirmed boundary;
- no rejected or crash/outlier lap changes `effective_lap_length_m`;
- every ambiguous/nonphysical visual candidate is rejected with a stable reason;
- uncertainty increases through missing/contradictory evidence and reaches unavailable instead of a long held plateau;
- no silent fallback to legacy `track_position` saturation;
- legacy 720p profile unit/integration tests remain green.

- [x] **Step 2: Convert each real failure into a generic RED test**

For every failed metric, extract only minimal numeric facts into a synthetic test—never an image crop, Spa coordinate, or video frame. Examples: a long zero-speed crash interval, a 40% visual branch jump, a false one-frame lap increment, or a 30% lap-distance outlier. Run the focused test and confirm it fails for the measured reason.

- [x] **Step 3: Implement the smallest generic correction and rerun both sessions**

Change validated configuration or the owning pure function. Run focused tests, full tests, clean replay, then crash-heavy replay. Both validation summaries must pass simultaneously; a robustness fix that regresses the clean 0.2-point spread is not accepted.

- [x] **Step 4: Remove obsolete production behavior only after both gates pass**

Delete the production call path to geometric start detection, unconditional backward hold, and `_apply_completion_handling()`. Keep a compatibility module only if an external import test requires it. Replace legacy assertions expecting `MISSING_HELD`, `BACKWARD_HELD`, `JUMP_CLAMPED`, or `FORCED_COMPLETION` with fused-contract assertions; do not merely delete coverage.

- [x] **Step 5: Perform final verification and documentation alignment**

```bash
./scripts/docs-list
PYTHONPATH=src .venv/bin/python -m compileall -q src scripts tests main.py run_server.py
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
git diff --check
git status --short --branch
```

Confirm with `rg -n -i 'spa|francorchamps|la source|raidillon|les combes|bruxelles|359, 0|70, 155' src tests config` that no circuit-specific production/test rule was introduced. References are allowed only in documentation and ignored validation output.

- [x] **Step 6: Commit the robustness gate atomically**

Stage only tracked source, tests, and aligned documentation. Inspect `git diff --cached --stat` and `git diff --cached` before committing:

```bash
git add src tests config scripts/diagnose_progress.py README.md docs/architecture.md docs/acc-ps5-plan.md docs/current-status.md
git commit -m "feat: replace legacy position with generic fusion"
```

Do not push. Leave `main` local and report its new ahead count and commit hash for explicit user validation.

## Final measurable acceptance checklist

- `s_odometry` passes exact synthetic distance tests and never invents observed distance through invalid speed gaps.
- Red extraction returns all plausible candidates even when a larger red region is present.
- Centerline output is a single ordered closed cycle; invalid topology is explicit and never falls back to the outline.
- Temporal scoring selects the odometry-consistent branch for the `0.015` versus `0.347` ambiguity and rejects ties.
- Only a confirmed `+1` lap transition after configured consensus anchors or resets fused progress.
- Opening partial laps remain unanchored; complete boundary-to-boundary laps can be rebased offline.
- `s_fused`, its component signals, source, uncertainty, and reasons reach normalized telemetry and diagnostic output.
- Long visual/speed uncertainty becomes unavailable, not observed or indefinitely held.
- Clean BMW repeated-checkpoint spread is `<= 0.002`; premature completions and unconfirmed resets are zero.
- Crash-heavy laps do not recalibrate lap length; degradation is explicit and the clean-session gates still pass.
- Existing 720p input remains readable; all unit tests, documentation discovery, compilation, and `git diff --check` pass.
- Raw videos and ignored full traces remain unmodified and uncommitted.

## Atomic commit sequence

1. `feat: define odometric progress contracts`
2. `feat: integrate speed into odometric progress`
3. `feat: retain plausible red map candidates`
4. `feat: build validated generic map centerline`
5. `feat: guide visual projection with odometry`
6. `feat: confirm trusted lap boundaries`
7. `feat: fuse progress with uncertainty and trusted anchors`
8. `feat: propagate fused progress through telemetry`
9. `test: validate fused progress on clean laps`
10. `feat: replace legacy position with generic fusion`

Each commit is contingent on focused and full GREEN tests. Extra fixes discovered by real replay receive their own regression-first commit between steps 9 and 10.
