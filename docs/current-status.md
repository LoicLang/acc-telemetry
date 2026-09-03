---
summary: single source of truth for current project state, active work, blockers, and exact next action
read_when:
  - starting any task
  - resuming work after another agent
  - changing project priorities or milestone status
---

# Current status

Last verified: 2026-09-03

This document is the mandatory living handoff for the repository. Update it from
verified evidence whenever active work, blockers, stage gates, or the next action
change. Use `git log` for authoritative commit hashes and dates.

## Current objective

Prepare the implementation of a circuit-generic fused `s`, using Spa as the first
validation dataset.

- Active milestone: generic fused `s` production correction
- Status: implementation in progress on `feature/generic-s-fusion`
- Active specification: `docs/superpowers/specs/2026-09-03-generic-s-fusion-design.md`
- Active plan: `docs/superpowers/plans/2026-09-03-generic-s-fusion.md`
- Last completed technical plan: `docs/superpowers/plans/2026-09-02-native-1080-and-s-diagnostics.md`
- Last completed plan: `docs/superpowers/plans/2026-09-02-agent-handoff-documentation.md`
- Technical ACC implementation: Tasks 1-8 complete; clean-session validation is next
- Documentation milestone: verified complete

## Resume here

1. Run `./scripts/docs-list`.
2. Read this document.
3. Read the active specification above; if an active plan is named, read it too.
4. Inspect `git status --short --branch` and `git log --oneline -10`.
5. Continue from the first unchecked plan step.

## Recently completed

- The generic fused `s` design was decomposed into a ten-commit TDD execution plan
  covering independent odometry, all plausible red candidates, a validated unique
  centerline, odometry-guided projection, confirmed lap anchors, fused uncertainty,
  domain propagation, and clean/crash-heavy local replay gates.

- Repository foundations and package boundaries were completed on 2026-08-31.
- The quality-aware `TelemetrySample` domain contract was added.
- CLI and web processing share `TelemetryPipeline`.
- The agent-handoff and telemetry-reliability design was recorded in commit
  `e870506`.
- Dynamic documentation discovery was added to that design in commit `67167a3`.
- The current documentation implementation plan was recorded in commit `720c3fd`.
- The tested documentation index was implemented in commit `595a6cf`.
- The mandatory handoff protocol and living status were added in commit `a581c19`.
- The ACC PS5 plan was corrected from the 2026-09-01 evidence in commit `457a1e1`.

## Active milestone progress

- Generic progress contracts and validated circuit-independent settings are implemented
  on `feature/generic-s-fusion`. The Task 1 RED tests failed on the missing contracts
  and settings; focused tests and the full 83-test suite then passed GREEN.
- Independent speed odometry now integrates observed speed with trapezoidal `v * dt`,
  interpolates only bounded internal gaps, preserves missing/anomalous evidence, and
  calibrates effective lap length from robust boundary-to-boundary medians. Task 2
  focused tests and the full 93-test suite pass.
- Red-map extraction now retains every independently plausible contour, rejects large
  backgrounds and low-circularity artifacts individually, supports both red HSV ranges,
  and returns stable candidate ordering. Task 3 focused tests and the full 98-test
  suite pass; the legacy single-largest-contour behavior remains characterized only.
- Generic centerline extraction now selects a dominant stable-map component, thins it,
  prunes local branches/marker cycles, rejects unresolved topology, orders one closed
  cycle, and resamples it by arc length. The original 1080p map ROI truncated the HUD
  cycle; the profile now covers the full left-side map region. On 59 sampled frames
  from the immutable clean BMW capture, the generic extractor returns 861 points and
  a 1490.639 px cycle. All 109 tests pass.
- Visual geometry now returns every compatible point-to-segment projection, including
  wraparound and nearby branches. Pure temporal selection scores normalized odometric
  error, centerline distance, and image displacement; it accepts only a clear winner
  and preserves missing, out-of-gate, and ambiguous reasons. All 121 tests pass.
- Raw lap observations now feed a pure confirmation state machine. Initialization and
  each sequential `+1` transition require five consecutive observations; missing,
  isolated, decreasing, and jumping values remain inspectable without emitting a
  boundary. The configured confirmer is constructed but does not yet reset production
  position. All 127 tests pass.
- The fused estimator now stays unavailable before a confirmed boundary, anchors only
  on that boundary, predicts from odometric distance, applies wrapped visual correction
  without implicit lap resets, and exposes interpolation, prediction, ambiguity, and
  uncertainty-limit reasons. Offline replay learns only from accepted complete laps;
  a synthetic crash-distance outlier cannot recalibrate the median. All 136 tests pass.
- CLI and web processing now construct the same generic session estimator. The shared
  pipeline collects raw frame evidence, then performs offline calibration/fusion and
  emits legacy `track_position` only as `s_fused * 100`. Modern output preserves
  component signals, uncertainty, source, and reasons. Speed OCR now distinguishes a
  fresh observation from held, missing, or anomalous evidence. A global OpenCV mock
  that made test results order-dependent was removed. All 146 tests pass.

- OCR runtime prerequisite: verified. `LapDetector` now discovers
  `data/shared/tessdata/eng.traineddata`, and the real tesserocr backend initializes
  successfully without a separate system Tesseract installation.
- Native 1080p profile: validated as `ps5_full_map_1080p` on ten manually
  annotated checkpoints from the clean BMW session.
- Native-versus-downscaled OCR comparison: complete. Native 1080p scored 10/10
  exact matches for lap number, last-lap time, speed, and gear. The identical
  Lanczos-downscaled 720p frames scored 9/10 for lap number, 0/10 for last-lap
  time, and 10/10 for speed and gear.
- Capture baseline decision: use native 1920x1080/60 FPS for future ACC sessions.
- OCR calibration finding: a tighter last-lap-time crop and thresholded 3x
  lap-number preprocessing were required; resolution alone was not sufficient.
- Position diagnostic contract: implemented and unit-tested. It exposes dot,
  closest index, anchor source, direction, raw position, forced completion,
  validated position, and decision without changing legacy numeric output.
- Position trace CLI: implemented and tested as `scripts/diagnose_position.py`; it
  writes ignored diagnostic CSV data without changing legacy telemetry records.
- Full clean-session position trace: collected over 139,561 rows and 2,326 seconds.

### Confirmed `s` root causes

The first invalid state exists before smoothing:

- geometric start anchor: pixel `(359, 0)`, path index `1141`;
- actual confirmed crossing: approximately `(70, 155)`, mapping variably to path
  indexes `1873`, `1904`, or `372`;
- first detected raw position: 21.7602% at 8.0167 seconds, immediately clamped from
  zero because it is relative to the wrong geometric anchor;
- first forced completion: 52.25 seconds;
- first `s >= 99.9%`: 52.3167 seconds;
- first plateau at or above 99.9%: 229.75 seconds, until the real transition.

The extracted map path is the outline of a thick white line rather than a unique
centerline. Adjacent red-dot pixels can therefore select physically adjacent but
topologically distant path indexes. One measured jump changed index `1905` to `370`
and raw position from about 1.51% to 34.68%.

Red-dot detection also selects the largest red contour before checking its size.
Transparent-map backgrounds frequently contain a red cockpit or car region above
4,000 px² plus a valid car dot around 160–195 px². The large contour is rejected and
the valid smaller dot is ignored.

Trace decision totals:

- `missing_held`: 63,282 frames;
- `backward_held`: 40,254 frames;
- `forced_completion`: 18,323 frames;
- `smoothed`: 16,460 frames;
- `jump_clamped`: 1,196 frames;
- directly `observed`: 32 frames;
- `lap_reset`: 14 frames.

The monotonic validator and forced-completion rule amplify and conceal the upstream
anchor, topology, and red-dot selection failures. They are not the first cause.

### Approved production direction

The replacement is generic across circuits and validated on Spa first:

1. `s_odometry` integrates `speed / 3.6 * delta_time` and is normalized by measured
   complete-lap distance;
2. `s_visual` projects plausible red-dot candidates onto a unique map centerline;
3. `s_fused` uses odometry as a temporal prediction and visual position as an absolute
   correction;
4. every output retains source, uncertainty, and reasons;
5. only a confirmed lap boundary anchors or resets progress.

Official circuit length is optional sanity evidence. It is not the primary distance
denominator. No Spa-specific coordinates or templates are allowed in the first
implementation.

Milestone commits:

- `e944f81`: discover repository-local OCR data;
- `d485cf2`: add the explicit native 1080p profile;
- `d7a6005`: calibrate 1080p OCR regions and lap-number preprocessing;
- `6b76631`: adopt native 1080p60 as the capture baseline;
- `54ac52f`: expose extraction-level position decisions;
- `b12bfe9`: add the shared-pipeline diagnostic trace;
- `0548b61`: record and characterize the confirmed position root causes.

Milestone verification: 77 tests pass, the diagnostic CLI processed all 139,561
frames, documentation discovery passes, and legacy telemetry output remains unchanged.

Verification for the documentation milestone:

- documentation index exits successfully and lists four active documents;
- all 64 repository tests pass;
- Python compilation succeeds for `src`, `scripts`, `tests`, and launchers;
- no telemetry production behavior was changed in this milestone.

Verification for the active generic fused `s` implementation plan:

- every local evidence path named by this document exists, including both immutable
  external captures;
- documentation discovery and `git diff --check` exit successfully;
- Python compilation succeeds for `src`, `scripts`, `tests`, and launchers;
- all 78 repository tests pass;
- no telemetry production behavior or raw video was changed while writing the plan.

## Verified working baseline

- Native ACC PS5 capture at 1920x1080 and constant 60 FPS is validated; historical
  1280x720 recordings remain supported.
- The static full-map HUD path is extracted.
- Controls, speed, and gears produce useful observations.
- Real lap transitions can be detected on the controlled short capture.
- Raw session videos remain immutable and ignored by Git.

## Confirmed blockers

### Longitudinal coordinate `s`

Status: failed validation; not safe for corner segmentation or lap alignment.

Evidence from the controlled Spa capture on 2026-09-01:

- `s` first reaches at least 99.9% at 88.033333 seconds in a 180-second capture;
- `s` remains at or above 99.9% for 50.027742% of frames;
- the real lap transition occurs around 178.2 seconds;
- after that confirmed transition, the reset produces plausible progress near zero.

The longer Spa session reproduces `initial_s_anchor: fail_reproduced`.

### Lap transitions on long captures

Status: failed validation.

The longer 2026-09-01 session records
`long_capture_lap_number_ocr: fail_false_transitions`. A false confirmed transition
can reset the position anchor, so this is a prerequisite for trustworthy `s` across
multiple laps.

### Quality propagation

Status: modeled but not connected end to end.

`TelemetrySample` supports field-level observed, missing, held, interpolated, and
anomalous states. The active pipeline and session CSV exports still contain legacy
records without field-quality or anomaly output.

## Local evidence

The following evidence is intentionally ignored by Git and may be absent on another
machine:

- `data/sessions/2026/2026-09-01_spa_ps5_capture-test/session.yaml`
- `data/sessions/2026/2026-09-01_spa_ps5_capture-test/processed/telemetry_20260901_182913.csv`
- `data/sessions/2026/2026-09-01_spa_ps5_braking-baseline-aborted/session.yaml`

New immutable external captures for the active milestone:

- `/Users/loiclang/Movies/2026-09-02 21-55-05.mov`: primary clean BMW session,
  1920x1080/60 FPS, 2326.033333 seconds, at least 12 visible laps;
- `/Users/loiclang/Movies/2026-09-02 22-40-01.mov`: secondary robustness session,
  1920x1080/60 FPS, 1137.016667 seconds, recent car change and crashes.

Ignored local A/B evidence:

- `data/lab/2026-09-02_native-1080-ocr/reports/ground-truth.csv`
- `data/lab/2026-09-02_native-1080-ocr/reports/ocr-results.csv`

Ignored local position evidence:

- `data/lab/2026-09-02_native-1080-position/trace.csv`

Verify these paths exist before using them. Their summarized findings above are the
durable repository record; personal videos and full telemetry exports must not be
committed.

## Priority order

1. Implement and validate the independent `s_odometry` baseline.
2. Make red-dot candidate extraction survive large red backgrounds.
3. Build a unique generic map centerline.
4. Fuse visual candidates with odometric prediction and trusted lap anchors.
5. Validate `s_fused` on clean then crash-heavy Spa evidence.
6. Confirm lap transitions robustly on long captures.
7. Propagate field-level quality and anomalies through the complete pipeline.

Corner segmentation, driving-event extraction, reference comparison, coaching
rules, dashboards, and generative feedback remain blocked until the reliability
gates pass on controlled Spa evidence.

## Current next action

Begin Task 9 in `docs/superpowers/plans/2026-09-03-generic-s-fusion.md`: add the
tested progress-diagnostic schema and metrics, then replay the immutable clean BMW
capture into ignored `data/lab/` output and evaluate every clean-session gate.
