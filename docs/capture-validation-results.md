---
summary: final A7 run-008 independent results, scoped denominators, exclusions and failed gate evidence
read_when:
  - assessing the A7 gate or planning development-only reliability corrections
  - comparing a new extractor fingerprint against the frozen run-008 benchmark
---

# A7 independent results — 2026-09-09

This page preserves the frozen A7 fingerprint and results. A8 changes modern speed
extraction; its separate new-code development measurements and remaining blockers
are in [fresh-measurement-results.md](fresh-measurement-results.md). No result below
is transferred as acceptance of the changed extractor.

**Gate A fails. B remains blocked.** Authoritative local evidence is under
`data/lab/coaching-reliability/run-008/reports/evaluation-final-v2/`.
`gate-a.json` in that directory supersedes earlier run-008 gates. The earlier reports
remain intact; `evaluation-final/` incorrectly treated generic release starts as
falling 5% crossings and nearby unannotated crossings as false positives. RED tests
correct those interpretation errors without changing extraction or A6 annotations.

| Check | Result | Evidence within the authoritative directory |
| --- | --- | --- |
| software_regressions | pass | gate links 24 focused, 9 diagnostic and 288 full-suite tests |
| lap_events | fail | historical.json: 0/5 approved increments detected |
| field_accuracy | fail | bmw.json, crash.json, holdout.json |
| field_coverage | pass | same three reports, only frozen short target segments |
| timebase | pass | all five source reports |
| holdout | fail | holdout.json and integrity.json |

## Fields

Fresh extraction and normalized quality are both required. Held or absent samples
remain in coverage denominators, but not error denominators. P95 uses linear quantile
interpolation. No tolerance is subtracted from an error.

| Source | Fresh speed / labels | Speed MAE / P95 km/h | Brake MAE points | Throttle MAE points |
| --- | ---: | ---: | ---: | ---: |
| BMW | 19 / 19 | 2.315789 / 9.0 | 0.973168 | 3.561060 |
| Crash | 20 / 21 | 1.7 / 6.0 | 1.600062 | 3.124183 |
| Holdout | 58 / 60 | 1.551724 / 5.15 | 0.729303 | 4.285403 |

Brake and throttle each have 19/19, 21/21 and 60/60 measured labels respectively;
100/100 total. Their original ±5-point annotation tolerance remains explicit.
All three speed sources fail the unchanged MAE 2 / P95 5 km/h targets. All pedal MAEs
pass the unchanged 5-point target. Pedal P95 values are published without inventing
a new P95 acceptance threshold. Holdout additionally has **6 fresh speed readings
on 20 approved absent-HUD frames**, at frames 32580, 32640, 32700, 32760, 32820, 32880.
Brake/throttle produce no observed value on those absent-HUD labels.

| Target scope | Speed fresh frames | Brake and throttle, each | Duration |
| --- | ---: | ---: | ---: |
| BMW: 14 segments | 564 / 564 (100%) | 564 / 564 | 9.4 s |
| Crash: 18 segments | 657 / 683 (96.1933%) | 683 / 683 | 11.3833 s |
| Holdout: 77 segments | 4175 / 4216 (99.0275%) | 4216 / 4216 | 70.2667 s |

These **109 segments, 5,463 frames, 91.05 s** were fixed from annotation windows
before reading the new pedal measurements. They are not whole-lap coverage. Target
selection establishes a denominator, not visibility truth or accuracy between labels.
The extra clean clip has no accepted field-accuracy truth and remains diagnostic.

## Events and uncertainty

Historical `part-0` contains 56,246 presentation frames. User approval of H01–H05
covers exactly five adjacent-frame counter-change pairs: 17762–17763, 26681–26682,
35481–35482, 44408–44409, 54054–54055. Independent agent review of all-frame temporal
counter extrema confirms stable digits between these pairs and no increment in the
four old suspect windows. The opening timed lap without a counter increment is
excluded by the operational definition. These are counter transitions, not physical
axle crossings. The pipeline emits zero boundaries: **recall 0/5; five misses; zero
predictions**, hence undefined precision/error P95/confirmation delay. No false
precision or zero timing error is assigned to missing detections.

Sparse A6 counter labels also match 2/2 on BMW (about 0.00833 s midpoint error each)
and 1/1 on crash (0.075 s). Confirmation delay is about 0.06667 s in all three pairs.
Those sparse labels do not establish exhaustive lap-event accuracy on these sources.

Pedal timing finally retains **16 onset/reapplication markers in 15 windows**, all
on the reserved source: 12/12 brake onsets matched, P95 **0.0474999 s**; 4/4 throttle
reapplications matched, P95 **0.00833345 s**. These compare first fresh 5% crossing
times with reviewed onset/reapplication midpoints; they are not a B4 detector score.
Two other nearby throttle crossings remain unannotated candidates, not proven false
positives. Reports publish all candidate/match counts and observable-window counts.

Ten original pedal markers are excluded from this metric, without changing A6:

- E16 reaches 100% at frame 30397, starting with approximately 60% throttle. It is not
  an onset; the initial estimate remains context without a quantitative tolerance.
- Two `first_visible_brake` markers do not establish applicable threshold semantics.
- Seven generic release markers show largely filled bars at the approved frame:
  B1/B2 throttle release and E04/E05/E08/E11/E19 brake release. They mark release
  starts, not passages below 5%. Both release-latency subtypes remain `not_evaluated`.
  The comparison offsets in the earlier diagnostic report are not extractor errors.

Interval half-widths (typically about 0.00833 s) and midpoint errors are distinct.
Human timing uncertainty remains unknown; single-frame resolution is not zero error.
There is no calibrated confidence interval or population generalization from these
small, selected and temporally correlated samples.

## Physical landmarks and timebase

| Source | Available passages | Circular range of normalized s |
| --- | ---: | ---: |
| BMW | 2 / 2 | 0.00012023316829146147 |
| Crash | 2 / 2 | 0.001578157761827348 |
| Holdout | 0 / 2 | not_evaluated (unanchored progress) |

All six physical annotations remain accepted. Availability of four estimates does
not change their truth. Reports retain each interval's values, midpoint offset,
quality, reasons and uncalibrated estimator uncertainty. These are repeated-passage
**dispersion** results; no metric spatial accuracy or conversion to meters is valid.

Exact ordered frame/timestamp alignment passes for historical 56,246, clean 18,902,
crash 29,402, BMW 47,589 and holdout 53,700 frames. Presentation/discard-packet checks
remain independent of nominal coded frame counts. The capture validator reads the
artifacts without OCR; separate production runs consumed newly reviewed visibility.

## Provenance and reproduction

A6 authority remains `run-007/processed/accepted-corpus-v4/index.json` and
`run-007/reports/a6-acceptance.json`. All original labels, approvals, recording IDs,
roles and source bytes were rehashed and preserved. New labels are derived copies:
`run-008/processed/agent-reviewed-corpus-v2/` and `historical-approved-v2/`.
Reviewed-visibility artifacts are `run-008/processed/{bmw,crash,holdout}-reviewed-session/`;
historical and extra clean artifacts retain their original `*-session/` paths.

Separate review evidence under `run-008/reports/`:
`user-historical-approval.json`, `agent-historical-review.json`,
`agent-visibility-review.json`, `pedal-semantics-review.json`, `input-integrity.json`.
The user explicitly requested autonomous reliable visual review. Agent reviews are
attributed as such, never retroactively attributed to the user's A6 approval.
Temporal min/max sheets incorporate every frame but do not preserve ordering; their
qualitative fixed-HUD visibility review does not prove numerical pedal accuracy.

All extraction modules and resolved extraction settings match the pre-inspection
holdout reservation. New visibility is an annotation input; no decoder or threshold
was fitted to holdout results. All original validation targets are unchanged.
The three A7 measurement-definition additions were fixed before capture results.

Final gate SHA-256:
`8b0d323bef702ce8e7dafa4e68c2be2c736f7c06b55d221c4a5ea8f8f6551373`.
Measurement fingerprint:
`d9808e44a6abfb24b78e33d14879409b61c7e727fbeaf6bb15dac67afaa50ae3`.
The gate contains per-source component/configuration fingerprints, file hashes and
absolute evidence paths; documentation-only commits do not invalidate them.

Local run drivers are preserved in `run-008/`: `verify_inputs.py`, review scripts,
`publish_final_v2.py` and `build_results.py`. They publish exclusively into new
outputs; do not rerun over existing directories. For a new single-source measurement,
use the CLI in `capture-validation.md` with a new output filename.

A8 executed the development speed RED correction and reproduced historical OCR
errors separately. The living next action is in `current-status.md`. Do not change
thresholds to pass, use holdout to fit corrections, or start B.
