---
summary: single source of truth for current project state, active work, blockers, and exact next action
read_when:
  - starting any task
  - resuming work after another agent
  - changing project priorities or milestone status
---

# Current status

Last verified: 2026-09-05

This document is the mandatory living handoff for the repository. Update it from
verified evidence whenever active work, blockers, stage gates, or the next action
change. Use `git log` for authoritative commit hashes and dates.

## Current objective

Implementation planning is complete for a first reference-based corner coaching
dossier. The user explicitly requires a relevant reference and visibility into the
driver's trajectory, not just comparisons of pedal traces. Implementation is now authorized, starting with reliability A0/A1.

Start with `docs/coaching-implementation-roadmap.md`. Execute reliability plan A
before dossier plan B; optional replay plan C remains separate and inactive.
The first intended result is a post-session debrief with one priority, an exercise,
and a measurable success criterion, supported by paired cockpit images and a sourced
reference explanation. Multi-week training and metric lateral ML remain later work.

### Audit findings superseding earlier reliability claims

- A1 corrects the audited raw-lap integration defect: production now uses strict,
  fresh `observe_lap_number()`. The legacy wrapper still smooths/holds intentionally.
  Real detector -> pipeline -> confirmer synthetic regressions verify missing reads,
  rejected jumps, isolated errors and one boundary after five fresh increments.
  This does not establish the false-boundary rate on real video.
- Speed provenance reaches fusion but is omitted from output records; normalization
  can turn HELD speed into OBSERVED. Earlier claims of end-to-end speed quality below
  are superseded by this finding.
- Black control ROIs become observed zero inputs. Position comparison fills absent
  intervals and extends partial laps; the typed comparison API strips modern progress
  provenance. These are confirmed software defects, not measured prevalence in video.
- Existing replay metrics remain valid internal-consistency results; their odometric
  checkpoints and completion tests are not independent spatial ground truth. Metric
  accuracy and confidence calibration remain unverified.
- Local evidence: `data/lab/2026-09-05-technical-audit/`, containing integration and
  metric counterexamples plus test logs. All 186 existing tests pass under Python
  3.13.2; documentation discovery and diff checks pass. No production code changed.
- Planning delivered: common specification, detailed reliability/dossier tasks,
  separate replay feasibility experiment, source-admission rules, seven metric
  definitions, target CLI/artifact formats and human review gates. A0/A1 are complete; later tasks remain unchecked. The suggested Spa/Bruxelles case and reference source
  must be verified on real inputs; no reference has been acquired.
- Planning verification: documentation discovery succeeds; all 186 existing tests
  pass, including the four focused documentation-index tests. Local plan links and
  frontmatter were checked. No executable source/configuration files were changed.

- Active milestone: A0/A1 complete; A2 speed/gear provenance next
- Previous milestone status: generic boundary visual-anchor robustness implementation
  and representative validation complete at `4a101a8`; the new BMW and both controls
  pass their replay gates with zero unconfirmed resets, nonlocal jumps, or premature
  completions
- Earlier milestone status: generic fusion implementation and representative validation complete;
  merged locally into `main` at `f7888ae`
- Current validation status: the isolated missing-boundary-dot gap is resolved and the
  first complete BMW lap now contains fused visual progress
- Active specification: `docs/specs/2026-09-05-reference-corner-coach-design.md`
  (planning specification; no production gates newly passed)
- Last completed specification: `docs/specs/2026-09-05-generic-boundary-visual-anchor-design.md`
- Generic fusion design reference: `docs/specs/2026-09-03-generic-s-fusion-design.md`
- Active plan: `docs/plans/2026-09-05-coaching-reliability.md`
- Downstream plan: `docs/plans/2026-09-05-reference-corner-dossier.md`
  (blocked until gate A passes)
- Optional research plan: `docs/plans/2026-09-05-replay-spatial-feasibility.md`
  (inactive; not a prerequisite for the visual-reference dossier)
- Last completed implementation plan: `docs/plans/2026-09-05-generic-boundary-visual-anchor.md`
- Prior completed implementation plan: `docs/plans/2026-09-04-temporal-centerline-selection.md`
- Prior milestone handoff record — Last completed implementation plan: `docs/plans/2026-09-04-temporal-centerline-selection.md`
- Earlier completed implementation plan: `docs/plans/2026-09-03-generic-s-fusion.md`
- Last completed technical plan: `docs/plans/2026-09-02-native-1080-and-s-diagnostics.md`
- Last completed plan: `docs/plans/2026-09-02-agent-handoff-documentation.md`
- Technical ACC implementation: Tasks 1-10 complete
- Documentation milestone: verified complete

## Resume here

1. Run `./scripts/docs-list`.
2. Read this document.
3. Read any active specification named above; otherwise read the last completed
   specification only when the current work touches its decisions. If an active plan
   is named, read it too.
4. Inspect `git status --short --branch` and `git log --oneline -10`.
5. If an active plan is named, continue from its first unchecked step; otherwise
   follow `Current next action` below.

## Recently completed

- A1 adds immutable `FieldObservation`, strict lap parsing, and fresh OCR in the
  generic pipeline. Crop/preprocessing and legacy smoothing remain compatible.
  Missing evidence restarts the candidate; transition exports retain first candidate,
  confirmation, and last fresh previous-lap times. Anchoring remains at confirmation.
- Verified: RED integration/timing logs preceded changes; 15 focused tests and all
  192 tests pass. Logs: `data/lab/coaching-reliability/run-001/a1-*.log`.
  Sustained plausible OCR errors can still pass consensus; no independent video
  validation was performed, and the consensus score is not an accuracy probability.


- Removed the repository's dependency on the former external workflow package.
  All dated working material now lives under neutral `docs/plans/` and `docs/specs/`
  paths, every active and historical link was updated, and mandatory skill headers
  were removed from the plans. `AGENTS.md` now defines plans as ordinary repository
  checklists governed only by the local testing, documentation, and commit rules.
- Documentation discovery excludes `docs/plans/` and `docs/specs/` in both default
  and `--all` modes. Focused tests cover this behavior and prevent the legacy workflow
  directory or instruction markers from returning to repository guidance.
- The corresponding global package under `.codex` and its discovery symlink under
  `.agents/skills` were moved to the macOS Trash. This is recoverable and affects
  future skill discovery; an already running Codex session may retain its initial
  in-memory catalog until restarted.
- Verification after the migration: all changed Markdown links resolve, documentation
  discovery and `git diff --check` pass, Python compilation succeeds, and all 187
  repository tests pass. No production telemetry behavior changed.

- The generic boundary visual-anchor correction was validated on all three required
  captures. The new BMW replay retains four exact boundary anchors and three accepted
  calibration laps at an effective 6962.810185 m. Sources are 29,704 fused, 228
  predicted, 17,653 missing, and 4 boundary-observed frames; no lap is rejected. The
  opening partial lap accounts for 17,182 unanchored rows, but the first complete lap
  after 286.366667 seconds is recovered with 8,515 fused rows, beginning at
  286.833333 seconds. Unavailable duration falls from 436.616667 to 294.216667 seconds.
  Maximum checkpoint spread changes from 0.003187 to 0.005740; no BMW spread threshold
  was specified for this gate, so retain this increase as comparison evidence.
- The clean control retains three exact boundary anchors, two accepted laps, effective
  length 6965.332176 m, maximum checkpoint spread 0.001547, and 13.166667 seconds
  unavailable. Sources are 17,907 fused, 202 predicted, 790 missing, and 3
  boundary-observed frames; no lap is rejected.
- The crash-heavy control retains four exact boundary anchors. Lap 6 remains rejected
  with `duration_outlier` and `calibration_lap_rejected`; two regular laps calibrate to
  6960.709491 m. Sources are 26,402 fused, 389 predicted, 8 interpolated, 2,599
  missing, and 4 boundary-observed frames. Its 0.017384 checkpoint spread and
  43.316667 unavailable seconds keep degradation explicit.
- All three replays record zero unconfirmed resets, zero nonlocal visual jumps, and
  zero premature completion entries. Their ignored traces and summaries are under
  `data/lab/2026-09-05-boundary-visual-anchor/`; no source video was modified.
- Final branch verification lists all active documentation, compiles `src`, `scripts`,
  `tests`, and both launchers, and passes all 186 tests. Diff checks are clean and a
  word-bounded search finds no circuit name or measured coordinate in production,
  tests, or configuration.

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
- The `multiple_cycles` root cause is confirmed. The broad 1080p map ROI contains
  stable white cockpit evidence below the minimap. On the failing BMW recording, the
  left mirror/sky component occupies 3,093 stable-mask pixels at ROI box
  `(x=36, y=363, width=101, height=45)`, while the actual closed map component is
  second at 2,763 pixels. The former `_single_component()` area-dominance rule
  therefore rejects the frame set before it evaluates the map topology. On the
  passing control, the map was only narrowly dominant at 2,825 pixels versus 2,796
  pixels across all remaining components. The failure is a generic component-selection
  defect exposed by car/cockpit imagery, not a malformed Spa map.
- Temporal centerline selection was fast-forward merged into local `main` at
  `7d332e5`; its feature branch was deleted after merged-result verification. The
  stable-white threshold is 0.60 and each disconnected component is evaluated
  independently; exactly one ROI-relative long closed cycle is accepted. No circuit
  shape, Spa coordinate, or car-specific crop is used.
- The corrected new BMW replay extracts the centerline and retains the same four
  confirmed boundaries, three calibration laps, and 6962.810 m effective length. It
  records zero unconfirmed resets, nonlocal jumps, or premature completions. Sources
  are 20,098 fused, 1,280 predicted, 10 interpolated, 4 boundary-observed, and 26,197
  missing frames; maximum checkpoint spread is 0.003187.
- The 436.617-second unavailable total is now explained. The 286.267-second opening
  partial lap is intentionally unanchored. At the first confirmed boundary, the red
  dot is missing on the exact confirmation frame, so no visual anchor is retained and
  the whole following 144.567-second lap remains unavailable. Later boundaries have
  a dot and their laps contain only about 1.8-2.0 unavailable seconds. This is a
  separate generic visual-anchor gap, not a centerline regression.
- The clean control still passes its 0.002 spread target at 0.001547, with 17,633
  fused frames and 13.167 unavailable seconds. The crash control still rejects lap 6
  for `duration_outlier`, calibrates to 6960.709 m from two accepted laps, records
  zero resets/jumps/premature completions, and exposes 43.300 unavailable seconds.

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

- Boundary visual-anchor recovery now retains compact irregular candidates and can
  recover only around an already confirmed lap boundary. Real-capture validation on
  the new BMW and both representative controls passes the planned boundary,
  calibration, safety, and clean-spread gates. Every real boundary in these captures
  used `boundary_anchor_exact`; the recovery paths remain covered synthetically.

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

Status: the generic replacement and isolated boundary-anchor correction pass the new
BMW plus clean and crash-heavy representative gates. The first complete BMW lap is
now fused, all eleven replayed boundaries anchor exactly, and all three captures retain
zero unconfirmed resets, nonlocal jumps, and premature completions. The historical
legacy failure below remains evidence for why the old tracker is not safe.

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

Status: fused progress provenance reaches records, but the comparison API strips it.
Speed provenance reaches fusion and is lost in output records. Complete field-level
quality for lap number, controls, gear, CSV/API consumers, and analysis remains
incomplete. See the audit and active plan A for reproduced defects and corrections.

`TelemetrySample` supports field-level observed, missing, held, interpolated,
predicted, fused, and anomalous states. The available contract does not imply every
extractor and consumer uses it correctly.

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
- `/Users/loiclang/Movies/2026-09-03 22-42-08.mov`: new BMW validation session,
  1920x1080/60 FPS, 793.166667 seconds, four confirmed boundaries.

Ignored local A/B evidence:

- `data/lab/2026-09-02_native-1080-ocr/reports/ground-truth.csv`
- `data/lab/2026-09-02_native-1080-ocr/reports/ocr-results.csv`

Ignored local position evidence:

- `data/lab/2026-09-02_native-1080-position/trace.csv`
- `data/lab/2026-09-04-new-1080-bmw/replay-after-fix/`
- `data/lab/2026-09-04-temporal-centerline-selection/`
- `data/lab/2026-09-05-boundary-visual-anchor/`

Verify these paths exist before using them. Their summarized findings above are the
durable repository record; personal videos and full telemetry exports must not be
committed.

## Priority order

1. Execute plan A2: speed/gear/lap provenance, then follow plan A through
   provenance, bounded comparison and independent historical/recent validation.
2. Only when A passes, execute plan B: acquire/admit a reference, review physical
   landmarks and trajectory images, compute seven metrics and export a ChatGPT dossier.
3. Review a real coaching response and measure the exercise at a subsequent session.
4. Consider optional plan C separately; no dataset/ML implementation is active.

Corner segmentation, driving-event extraction, reference comparison, coaching
rules, dashboards, and generative feedback remain blocked until the reliability
gates pass on controlled Spa evidence.

## Current next action

Execute A2 in `docs/plans/2026-09-05-coaching-reliability.md`: add
`tests/test_quality_roundtrip.py` and run it RED before changing speed/gear records.
Continue on `codex/coaching-reliability`; A0 baseline commit is `7f60245`, with 187
passing tests (186 audit tests plus the workflow-removal guard). Both audit scripts
reproduced the defects before A1. The old integration script uses the historical
wrapper and obsolete fake interfaces: preserve it as baseline evidence; the tracked
A1 tests exercise current production. Python 3.13.2, ffmpeg/ffprobe and all handoff
video/evidence paths were verified present. No source video changed.
Gate A remains unvalidated, B blocked, C inactive. No push authorized.
