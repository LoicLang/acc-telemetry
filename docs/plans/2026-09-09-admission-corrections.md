---
summary: separate RED-first corrections for source-bound speed visibility, numerical admission and historical lap OCR after A8
read_when:
  - implementing the remaining A8 reliability corrections
  - preparing new development measurements before independent acceptance
---

# A9 — Admission and historical OCR corrections

Authorized after A8 on 2026-09-09. Specification: `docs/signal-treatment.md`.
Baseline: `b5eb04c`; evidence remains frozen under run-010. New outputs: run-011.
Only explicitly selected models below GPT-6 Astra may receive delegated work.
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

- [ ] Review the prepared 32-segment / 1,247-frame speed visibility dossier with
  explicit reviewer identity and uncertainty, preserving all previous approvals.
- [ ] Review complete calibration-lap speed visibility and replay admission/progress;
  do not infer whole-lap readability from short target segments.
- [ ] Reserve and evaluate a distinct independent recording before any inspection,
  after development choices are frozen. Keep missing latency truth not_evaluated.

New independent recording reservation follows the completed development corrections,
before inspecting the new recording. The known run-008 holdout stays historical.
