---
summary: single source of truth for current project state, active work, blockers, and exact next action
read_when:
  - starting any task
  - resuming work after another agent
  - changing project priorities or milestone status
---

# Current status

Last verified: 2026-09-04

This document is the mandatory living handoff for the repository. Update it from
verified evidence whenever active work, blockers, stage gates, or the next action
change. Use `git log` for authoritative commit hashes and dates.

## Current objective

Validate circuit-generic fused `s` against new native 1080p sessions before starting
corner analysis.

- Active milestone: new-session generic `s` robustness
- Previous milestone status: implementation and representative validation complete;
  merged locally into `main` at `f7888ae`
- Current validation status: lap confirmation and odometric calibration pass on the 2026-09-03 BMW
  session, but visual centerline extraction fails with `multiple_cycles`; production
  code is unchanged and the local merge remains unpushed
- Active specification: `docs/superpowers/specs/2026-09-03-generic-s-fusion-design.md`
- Active plan: `docs/superpowers/plans/2026-09-03-generic-s-fusion.md` (complete)
- Last completed technical plan: `docs/superpowers/plans/2026-09-02-native-1080-and-s-diagnostics.md`
- Last completed plan: `docs/superpowers/plans/2026-09-02-agent-handoff-documentation.md`
- Technical ACC implementation: Tasks 1-10 complete
- Documentation milestone: verified complete

## Resume here

1. Run `./scripts/docs-list`.
2. Read this document.
3. Read the active specification above; if an active plan is named, read it too.
4. Inspect `git status --short --branch` and `git log --oneline -10`.
5. Continue from the first unchecked plan step.

## Recently completed

- The previously unanalysed `/Users/loiclang/Movies/2026-09-03 22-42-08.mov`
  BMW session was replayed with `ps5_full_map_1080p`. All 47,589 processed frames
  preserve a clean raw/confirmed sequence from lap 0 through lap 4. Boundaries at
  286.367, 431.433, 577.417, and 722.617 seconds calibrate three complete laps to an
  effective 6962.810 m. There are zero unconfirmed resets and zero premature
  completion entries.
- That replay does not validate fused progress: stable-map preparation rejects the
  visual topology as `multiple_cycles`. The result contains 47,469 missing, 116
  predicted, and 4 boundary-observed frames, with 791.133 seconds unavailable. This
  is a safe failure rather than a fabricated coordinate, but it reopens centerline
  robustness for the current recording format. Ignored evidence is under
  `data/lab/2026-09-04-new-1080-bmw/replay/`.

- `feature/generic-s-fusion` was fast-forward merged into local `main` on 2026-09-04.
  The merged result passes all 158 tests and Python compilation. The feature branch is
  safe to delete after this handoff update; `main` has not been pushed after the merge.
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
  boundary. Production fusion anchors only on the resulting confirmed boundary. All
  127 tests passed at that implementation slice.
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
- Clean-session validation first replayed all 139,561 extracted frames. That run exposed
  session-global odometry uncertainty leaking across lap boundaries and two biased
  diagnostic metrics; each defect received a synthetic RED regression before correction.
- Per the user's 2026-09-04 direction, subsequent video checks use small representative
  derived clips. The clean clip covers source time 275-590 seconds, three confirmed
  boundaries, two complete calibration laps, and 18,902 extracted frames. It learns an
  effective distance of 6965.332 m, records zero unconfirmed resets, zero nonlocal jumps,
  zero premature completion-band entries, and a maximum interpolated checkpoint spread
  of 0.001522 across 99 checkpoints, passing the 0.002 target. Source counts are 17,673
  fused, 474 predicted, 3 interpolated, 749 missing, and 3 boundary-observed frames.
  The derived video, trace, and JSON summary remain ignored under `data/lab/`.
- The representative crash-heavy clip covers four confirmed boundaries and three
  complete laps. Two regular laps calibrate `effective_lap_length_m` at 6960.709 m;
  the 177.85-second degraded lap is rejected with `duration_outlier` and cannot alter
  calibration. The trace records zero unconfirmed resets, zero nonlocal jumps, and zero
  premature completion-band entries. It deliberately exposes degradation: checkpoint
  spread rises to 0.016398 and 43.1 seconds become unavailable instead of being held as
  observed. Source counts are 26,124 fused, 680 predicted, 8 interpolated, 2,586
  missing, and 4 boundary-observed frames.
- The final robustness fixes infer centerline direction only after one orientation wins
  against odometry by a configured margin, reject duration outliers as well as distance
  outliers, and keep the legacy tracker outside production CLI/web construction. The
  complete repository suite contains 158 passing tests.

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

Status: generic replacement implemented; representative clean and crash-heavy gates
pass. The historical legacy failure below remains evidence for why the old tracker is
not safe.

Evidence from the controlled Spa capture on 2026-09-01:

- `s` first reaches at least 99.9% at 88.033333 seconds in a 180-second capture;
- `s` remains at or above 99.9% for 50.027742% of frames;
- the real lap transition occurs around 178.2 seconds;
- after that confirmed transition, the reset produces plausible progress near zero.

The longer Spa session reproduces `initial_s_anchor: fail_reproduced`.

### Lap transitions on long captures

Status: confirmation state machine implemented and validated on the full 139,561-frame
clean replay plus both representative clips. The earlier 2026-09-01 false-transition
capture has not been replayed end to end with the new confirmer and remains a separate
verification item.

The longer 2026-09-01 session records
`long_capture_lap_number_ocr: fail_false_transitions`. A false confirmed transition
can reset the position anchor, so this is a prerequisite for trustworthy `s` across
multiple laps.

### Quality propagation

Status: fused progress and speed provenance are connected end to end. Complete
field-level quality for lap number, controls, gear, CSV/API consumers, and analysis
remains incomplete.

`TelemetrySample` supports field-level observed, missing, held, interpolated,
predicted, fused, and anomalous states. Progress and speed use this evidence; the
remaining fields and consumers do not yet propagate it completely.

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

1. Diagnose the generic `multiple_cycles` centerline failure on the new 2026-09-03
   BMW 1080p session without adding circuit-specific rules.
2. Convert the smallest confirmed generic cause into a RED regression, correct it,
   and rerun this BMW session plus the previously passing representative clips.
3. Replay the historical 2026-09-01 long capture through the new lap confirmer.
4. Propagate field-level quality and anomalies for lap number, gear, and controls.
5. Version or document CSV/API compatibility for the expanded progress contract.
6. Only after those gates pass, validate one manually reviewed corner segment.

Corner segmentation, driving-event extraction, reference comparison, coaching
rules, dashboards, and generative feedback remain blocked until the reliability
gates pass on controlled Spa evidence.

## Current next action

Explain and design the smallest diagnostic that identifies which stable white-map
components create the `multiple_cycles` result on the new BMW session. Do not tune a
Spa coordinate or change production behavior before that evidence exists. Push local
`main` only after explicit user request, and do not start corner analysis before the
reopened `s` gate and remaining quality gates pass.
