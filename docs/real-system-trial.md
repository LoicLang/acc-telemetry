---
summary: owner-approved priority for an end-to-end development trial with visible outputs and bounded video checks
read_when:
  - resuming work after the completed BMW and incidents counter reviews
  - deciding whether further exhaustive annotation is needed before showing the system
---

# Priority: try the complete system

Completed12 September2026: [run-023 result](real-system-trial-results.md). The
original execution contract below is preserved; do not repeat the trial by default.

After viewing run-023, the owner clarified the intended experiment: extract the whole
video automatically and use annotations only to verify quality afterward. This takes
priority over the sparse-review extraction prerequisite below. Follow
`automatic-system-trial.md`; retain run-023 as the reviewed-mode diagnostic baseline.

The owner considers the exhaustive review effort excessive and now prioritizes a
concrete end-to-end trial. The next delivery is a usable, inspectable output from an
existing real video, with an honest account of defects and missing data. Do not start
another exhaustive visual campaign or reviewer qualification before this delivery.

This is development work within A. A failing Gate A does not prevent running and
showing the current system; it still prevents admitting trustworthy downstream coaching.
No acceptance threshold, visibility contract or B/R restriction is relaxed.

## Execution

1. Read the living handoff and active A9 plan. Reuse the frozen counter truth from
   run-021/022 after integrity checks; do not repeat its visual annotation.
2. Process the complete incidents recording through the actual shared application
   pipeline exposed by CLI/web. Verify native1920×1080, exactly60fps CFR before new
   decoding. Use existing source-bound visibility evidence and a fresh output directory
   (run-023 if free). Preserve source files and all prior runs.
3. Open the actual generated report in the app. Show speed/brake/throttle curves,
   detected laps, missing-data coverage and available progress. Missing calibration or
   `s` is an observed limitation to display, not a reason to postpone the demonstration.
   A separate experimental viewer is unnecessary if the existing report suffices.
4. Compare counter observations/events mechanically against the complete frozen truth.
   For practical visual QA, select a small explicit set of video windows covering a
   substantial braking phase, acceleration, an incident and a lap boundary. Record their
   times, inspect the source and report together, and report action timing, obvious
   numerical errors, fabricated/held values and gaps. These windows are scoped checks,
   not exhaustive speed/pedal truth or independent acceptance. Do not convert unchecked
   frames into reviewed visibility. Show gaps where existing evidence is sparse.
5. Fix only demonstrated defects that prevent processing or materially misrepresent the
   displayed result. Before behavior changes add focused regressions; run focused/full
   tests before each commit. No threshold search for a green gate, broad refactoring,
   pedal smoothing or reconstructed measured speed. Re-run only affected work.
6. Deliver clickable output, what is useful today, concrete remaining blockers and one
   next action. Update current-status and plan checkboxes; commit/push the authorized
   branch without merging. Conserve quota: no agents unless newly requested.

A later independent trial should use a distinct new recording, ideally another circuit,
with extractor/settings frozen and reservation before any inspection. Do not request
that recording as a prerequisite for the existing-video demonstration. The known
historical holdout remains frozen and cannot become independent again.
