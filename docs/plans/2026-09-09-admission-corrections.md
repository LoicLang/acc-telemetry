---
summary: separate RED-first corrections for source-bound speed visibility, numerical admission and historical lap OCR after A8
read_when:
  - implementing the remaining A8 reliability corrections
  - preparing new development measurements before independent acceptance
---

# A9 — Admission and historical OCR corrections

Sequencing update12 September2026: the remaining independent acceptance work is
carried by the [local GPT delivery plan](2026-09-12-local-gpt-coaching-delivery.md).
The owner currently requests planning only; no new extraction/implementation begins
from this old next-step checkbox. Existing completed evidence remains frozen.

## Latest source-scope decision

- [x] Restrict all new video extraction/preparation to native 1920×1080 at exactly
  60 fps CFR; metadata/cadence refusal before frame extraction or OCR.
- [x] Set active CLI/web defaults to 1080p and preserve old artifacts read-only.
- [x] Retire further 720p work. Historical 5/5 remains archival evidence and does
  not replace an exhaustive 1080p event review. Gate A remains blocked.

The completed historical tasks below predate this decision and must not be rerun.

Authorized after A8 on 2026-09-09. Specification: `docs/signal-treatment.md`.
Baseline: `b5eb04c`; evidence remains frozen under run-010. New outputs: run-011.
Default delegation uses explicitly selected models below GPT-6 Astra. On 11 September
the owner explicitly authorized a bounded Astra visual experiment; its scope and
result are recorded in `docs/astra-review-trial.md`.
No holdout inspection/tuning, acceptance target change, pedal smoothing, R or B.

## C1 — Source-bound speed HUD visibility

- [x] Verify Git, existing evidence and hashes before modifications.
- [x] RED through real `observe_speed` and pipeline: unreviewed digits must not
  reach odometry as observed speed. Preserve original raw text.
- [x] Implement visible/absent/unknown reviewed intervals bound to source SHA/size;
  unknown by default, half-open bounds, nonempty reviewer and strict interval checks.
- [x] Guard black/empty ROI even inside visible intervals; no old speed reuse.
- [x] Preserve source/reviewer evidence through CLI, web service, config and artifacts;
  reject a review bound to another source when processing, exporting or reloading.
- [x] Complete focused/full tests, documentation and atomic commit (303 tests).
- [x] Produce new development replay evidence using independently reviewed speed
  spans; do not silently turn old pedal spans into speed visibility truth.

## C2 — Numerical speed admission

- [x] RED real reads for known 162→4/177→7 errors and other development support.
- [x] Inspect segmentation/admission alternatives without a threshold search for a
  green gate. Preserve fresh values, valid dynamics, raw text and one OCR read.
  Global single-word mode is rejected after 86-frame expanded development comparison.
- [x] Implement only an evidenced correction; uncertain or rejected readings remain
  absent, never median/held/reconstructed OBSERVED values. Any temporal rule must
  use real delta-t and explicit resets on gaps/context changes.
  Predeclared 100 m/s² / 0.25 s policy; cached 86-frame check gives 83 exact,
  three abstentions, no admitted errors. Full source validation remains below.
- [x] Verify ramps, minima, invalids, gaps, recovery, odometry/calibration/s; publish
  all denominators and new fingerprints. Commit separately from C1 and C3.

## C3 — Historical lap OCR

- [x] Use real reviewed H01–H05 endpoints and actual OCR inputs to compare a small
  justified set of segmentation/preprocessing options on development only.
  Foreground-bound thresholded ink with a one-pixel margin gives 10/10 versus 5/10;
  retain word mode and all digit components. Constructed multi-digit 12 still fails,
  so this is not unrestricted counter accuracy evidence.
- [x] Add RED regressions before the selected correction; keep multi-digit support,
  modern freshness and explicit legacy behavior. Restore shared OCR settings.
  Four focused tests and real 5/10→10/10 endpoint RED/GREEN; 307 full-suite pass.
- [x] Re-evaluate historical transitions on the full development source; preserve
  approved events, rejected suspects and author attribution. Commit separately.

## Publication

- [x] Freeze final extraction/settings before new replays. Preserve all prior runs.
- [x] Publish six scoped checks with compatible fingerprints; unavailable independent
  holdout and missing latency truth stay `not_evaluated`. Gate A must not pass early.
- [x] Rehash original inputs; synchronize handoff/results, run focused/full tests,
  `./scripts/docs-list` and `git diff --check` before each commit; push authorized
  branch only. No merge to main.

Final evidence: `run-011/reports/gate-a-final.json`, per-source `*-evaluation-v2.json`
and `development-results-v2.json`. All 133,237 frames replayed; historical 5/5,
BMW 2/2, crash 1/1 approved event matches. A global crop regression on BMW was found,
preserved and fixed by scoping it to 720p. Actual speed outcomes are 83 exact/3 absent
of 86 reviewed cells; 314 tests pass. Gate A still fails coverage and lacks complete
field/independent evidence; calibration and `s` are unavailable under sparse review.

## Remaining evidence work

- [x] Record the approved product order: A → useful B with mandatory visual
  trajectory review and exercise follow-up; metric `d` deferred until an evidenced
  limitation justifies separate research. No B/C execution started by this decision.

- [x] Review the prepared 32-segment / 1,247-frame speed visibility dossier with
  explicit reviewer identity and uncertainty, preserving all previous approvals.
  Run-014: all cells readable; scoped fresh admission 564/564 BMW, 679/683 incidents.
  V-CRASH-15 remains 28/31, below 95%; whole-lap and independent gates remain open.
  Evidence and limitations: `docs/speed-visibility-results.md`.
- [x] Freeze and prepare the first complete BMW calibration-lap dossier: run-015,
  frames 17160–25888 with padding; counter boundaries separately reviewed.
- [x] Review every frame of that complete-lap dossier: 8,729 readable cells,
  separately attributed to two gpt-5.6-sol reviewers; no inferred numerical truth.
- [x] Replay admission/progress with the complete calibration-lap visibility;
  run-015 full BMW replay: one accepted lap, 8,679/8,705 fresh speed observations,
  `s` available on 8,473 lap frames. No whole-source or independent accuracy claim.
  Evidence and interpolation limits: `docs/calibration-lap-results.md`.
- [x] Prepare exhaustive native1080p BMW/incidents counter media: run-016,
  76,991 ordered frames / 803 sheets, bound hashes and preserved prior annotations.
  L2 timer reset10→11 and numeric counter14→15 are separately recorded; no relabelling.
  Preparation and limits: `docs/lap-counter-dossier.md`.
- [x] Complete exhaustive fixed numeric-counter ROI review on BMW/incidents via
  primary unique-state inspection and exact source-frame mapping, then evaluate
  compatible counter events. Run-021/022 cover76991frames,8/8events, zero misses/extras.
  This replaces the rejected sustained source-sheet reviews; it is not a claim that
  all803 original sheets were manually read. Timer reset and numeric events stay distinct.
- [x] Run the explicitly authorized bounded Astra qualification: run-019,
  1,355/1,355 presentations agree (1,348 distinct frames), 8/8 brackets exact.
  This is a small method trial; sustained/exhaustive review remains unqualified.
- [x] Freeze and assess the contiguous40-sheet BMW batch with predeclared native QA.
  Sustained Astra labels rejected. Replacement primary exact-state review covers all
  3840frames/366states with21/21 QA agreement; no original-sheet manual-review claim.
- [x] Complete BMW fixed-ROI primary review and compatible event/observation evaluation.
  Run-021:4159 reviewed states mapped byte-exactly to47589frames; all47589 fresh counter
  observations exact;4/4 events, zero misses/extras, P95 8.3ms. BMW ROI scope only;
  incidents/global gate and independent validation remain open.
  Method, evidence and limits: `docs/exact-counter-state-review.md`.
- [x] Complete incidents fixed-ROI review and compatible event/observation evaluation.
  Run-022:24267 states/29402frames;29402 observed counter values exact,4/4events,
  P95 8.3ms. Isolated counter-path scope, no full telemetry-v2 freshness/parity claim.
  Evidence/limits: `docs/incidents-counter-results.md`.
- [x] Run the existing incidents capture through the actual shared telemetry pipeline,
  compare counters to frozen run-022 truth and retain speed abstentions.
- [x] Open/show the generated report, including curves, laps, missing data and available
  progress. Complete bounded video-aligned QA on braking, acceleration, incident and
  lap-boundary windows; deliver usefulness and concrete blockers to the owner.
  Owner priority: `docs/real-system-trial.md`. No further exhaustive annotation or
  reviewer qualification before this end-to-end demonstration. Fix only material
  evidenced defects; Gate A still blocks trustworthy coaching, not this trial.
  Run-023 delivered:29402 frames, counters exact4/4, speed679/pedals683 available,
  no s. Misleading pedal fill across gaps corrected with RED/GREEN;33 focused/318
  full tests. See `docs/real-system-trial-results.md`.
- [x] Apply the owner's12 September clarification: automatic full-video extraction,
  with annotations used only for subsequent validation, not as extraction permission.
  Explicit shared CLI/web mode preserves unverified provenance and existing defaults.
- [x] Finish run-024 automatic incidents replay, compare existing annotated zones,
  show continuous curves and scoped errors, and publish verification/commit/push.
  Result: speed29298/29402, pedals29402/29402; speed21/21 exact, pedal MAE1.60/3.12;
  counter29402 exact/4events. See `docs/automatic-system-trial.md`.
- [ ] Reserve and evaluate a distinct independent recording before any inspection,
  after development choices are frozen. Keep missing latency truth not_evaluated.

New independent recording reservation follows the completed development corrections,
before inspecting the new recording. The known run-008 holdout stays historical.
