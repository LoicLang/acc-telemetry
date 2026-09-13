---
summary: A8 fresh measurement evidence and distinct unresolved HUD, historical OCR and independent validation work
read_when:
  - assessing A8 implementation and development results
  - resuming separate HUD or historical OCR corrections before Gate A acceptance
---

> Historical evidence only — archived13 September2026. Old instructions, gates and next actions below are not current. Follow [current status](../../current-status.md).

# A8 fresh measurements — 2026-09-09

This page preserves A8 results and its fingerprint. Later corrections are recorded
in `admission-correction-results.md`; these old measurements are not transferred
to the changed code.

Gate A remains blocked. New evidence lives under ignored
`data/lab/coaching-reliability/run-010/`; run-008 and run-009 remain frozen.
S1–S3 are implemented. S4/S5 have been executed within available development
evidence; new independent acceptance remains open after the separate A corrections.

## Fresh speed and legacy compatibility

`reports/s1-red.txt` records five real extraction/pipeline tests and six functional
failures, including 246→255 and 179→188. Only OCR text was controlled;
`observe_speed` was not replaced by a mock. `s2-green.txt` records five passing
regressions. `s2-speed-ocr-portable.txt` records 16 passing OCR/legacy tests, and
`s2-speed-ocr-no-tesserocr.txt` verifies shared-mode restoration without installed
Tesserocr symbols. Tests cover ascending/descending histories, one OCR call,
invalid/mixed/nonfinite text, empty ROI, backend failure, gap and fresh recovery.

The modern observation publishes complete ASCII decimal text within the existing
0–400 km/h range. Empty/failed reads are missing; malformed/out-of-range readings
are anomalous with no numeric value. Original text and reasons survive.
There is no trailing median, history recovery or new temporal rejection threshold.
The explicit `extract_speed` legacy wrapper retains median/holding/recovery.
Old HELD artifacts keep their provenance. Numeric validity alone is not HUD validity.

## Propagation, pedal dynamics and odometry

`reports/s3-api-time-red.log` records two failures: default CSV float parsing changed
1/60 s to a neighboring float in the web API. The storage reader now uses round-trip
float parsing. `s3-green.log` records four passing end-to-end regressions;
`s3-focused.log` records 91 passing focused tests. Real pedal pixels/decoder and real
speed observations pass through pipeline, normalization, telemetry-v2, reloading and
the typed API with original values, frame/time, raw evidence, reasons and quality.
Old HELD observations retain their last fresh time and are not relabelled OBSERVED.

Synthetic 0→100/100→0, maximal then degressive braking, brief interruption, blip and
black-HUD absence survive exactly. There is no pedal filtering or fabricated ramp.
Odometry receives fresh speed or explicit missing/anomalous values. Existing internal
short-gap interpolation retains `speed_gap_interpolated` provenance; a tested 0.2 s
gap integrates 2 m at 36 km/h, whereas a 0.4 s gap exceeds the unchanged 0.25 s bound
and contributes no interval distance. The source speed remains absent in both cases.
This synthetic integration check is not a spatial accuracy claim. Calibration and
normalized `s` require the separate full-development replay evidence below.

## Separate speed HUD contract, still failing

`reports/hud-contract-current.json` is a controlled-backend development probe, not
empirical detector accuracy. Visible readable HUD permits a fresh value; absent
or unknown context must abstain; a return to readable HUD must start fresh.
The current method has no visibility-context input. The probe exposes admission of
plausible digits in menu, black-ROI, non-HUD numeric and unknown contexts.
No rule derived from the six known holdout errors was introduced.

Next isolated RED: pass source-bound reviewed speed visibility with explicit
visible/absent/unknown intervals through the real pipeline. Cover menu, black ROI,
numeric text outside HUD and return to HUD, preserving text/reasons and half-open
times. Only reviewed readable visibility may admit coaching speed; unknown must
remain absent. Before implementation, define source identity/reviewer validation
and obtain development context images independently of model outputs. Existing
control spans cover only pedals/steering and must not implicitly approve speed.
An automatic detector requires its own development evaluation.

## New full development replay

Artifacts: `processed/bmw-fresh-session/` and `processed/crash-fresh-session/`.
Code/config/labels/visibility were frozen before actual OCR extraction in
`reports/{bmw,crash}-replay-freeze-v2.json`. Initial interrupted attempt logs/freezes
remain preserved; final replay logs end with FINISHED. Measurement uses
`scripts/validate_capture.py` without OCR, with canonical reports
`reports/evaluation/bmw.json` and `reports/evaluation/crash.json`.

| Source | Fresh annotated speed | Speed MAE / P95 km/h | Fresh fixed-segment speed | Brake / throttle MAE points |
| --- | ---: | ---: | ---: | ---: |
| BMW | 19/19 | 0 / 0 | 564/564 | 0.973168 / 3.561060 |
| Crash | 21/21 | 0 / 0 | 681/683 | 1.600062 / 3.124183 |

Pedals remain 564/564 and 683/683 on the fixed segments, with all 40 annotated
points fresh per field. The 32 segments cover 1,247 frames (20.7833 s), not full-lap
coverage. No annotation tolerance is subtracted from errors. Old speed MAE/P95 was
2.315789/9 on BMW and 1.7/6 on crash (20/21 fresh). These are development comparisons.

All 76,991 source frames align with independent frame/timestamp evidence. Across
the full recordings, BMW has 47,470 observed / 105 missing / 14 anomalous speed
frames; crash has 29,303 / 95 / 4. Raw OCR text changed on **zero frames** versus
the old artifacts. Pedal observations also changed on zero frames. Full-source
fresh availability is not a claim of full-source accuracy or reviewed HUD visibility.
Syntactically valid wrong OCR remains possible; ranked large jumps in the numerical
diagnostics are not rejected by a new threshold or silently repaired.

`reports/{bmw,crash}-fresh-comparison-v2.json` contain per-point raw and output errors,
quality/reasons, gaps, ranked adjacent changes, and ±60-frame annotation neighborhoods
with minima/availability. Earlier comparison snapshots are preserved; use v2.
Separate direct image review `agent-development-speed-review.json` covers 44 frames
in four chronological windows, including four original annotation points. It yields
43 fresh exact outputs and one abstention: crash 21004 shows 38, OCR reads `638`,
so output is anomalous/null. The old output was HELD 73. Do not add 44 to the original
40 denominator without accounting for overlap. The fresh error denominator is 43;
these selected, correlated frames do not establish population accuracy.

An additional, separately attributed review of six frames selected from the largest
output jumps confirms **two admitted OCR errors**: BMW 20372 shows 162 but outputs 4,
and crash 8029 shows 177 but outputs 7. Both are OBSERVED with empty reasons;
their absolute errors are 158 and 170 km/h. Four neighboring frames are exact.
Evidence: `reports/evaluation/agent-outlier-speed-review.json` together with
`agent-outlier-speed-review-supplement.json` in the same directory. The immutable
supplement corrects manual newline escaping and model attribution from the dispatch
record (requested GPT-5.6 Sol/medium; serving runtime not independently verified),
while preserving the visual reviewer and original report. This selection is
conditioned on model output and is diagnostic, not a new independent sample. It
demonstrates a remaining numerical admission defect beyond the fixed 40-point result.
Do not fix it by restoring legacy holds or tuning on holdout; any future rejection
must abstain with raw evidence, respect real delta-t and preserve valid dynamics.

`reports/evaluation/development-summary-v2.json` summarizes the compatible outputs,
hashes and old/new calibration. It separates old numeric HELD diagnostics from
old fresh-only errors, avoiding an inflated baseline error denominator.

## Calibration and normalized progress consequences

`reports/{bmw,crash}-progress-calibration.json` and comparison v2 reports preserve
the replayed calibration/integration and complete provenance. BMW accepts three
laps with effective integrated length 6961.872685 m (old 6962.914352 m); crash
accepts two with 6960.322917 m (old 6960.833333 m) and rejects one duration outlier
under unchanged settings. Old calibrations were recomputed from old observations
with the unchanged calibration implementation.
These lengths are internal calibration quantities, not measured circuit truth.

| Source | Old → fresh total integrated distance m | Old → fresh available s frames | Maximum paired circular s change | New landmark circular range |
| --- | ---: | ---: | ---: | ---: |
| BMW | 37212.761574 → 37208.319444 | 29593 → 29591 | 0.000246748 | 0.000119935 (2/2) |
| Crash | 21671.000000 → 21676.648148 | 26822 → 26846 | 0.000121179 | 0.001578565 (2/2) |

Paired progress denominators are 29,591 and 26,818. Two BMW frames lose availability;
the change is reported, not masked by recalibrating thresholds. Previous landmark
ranges were 0.000120233 and 0.001578158. These small changes are dispersion and
internal consistency results only; no metric spatial accuracy or conversion of `s`
error to meters is justified. Estimator uncertainty is not calibrated confidence.

## Separate historical OCR diagnostic, still failing

`reports/history-counter-diagnostic.json` reproduces five incorrect readings on
ten H01–H05 endpoints using the real 720p detector: 0→7, 2→20 and 3→30.
`history-counter-agent-review.json` attributes direct visual inspection to
`codex-agent-historical-diagnosis`, separately from the original user approval.
Actual thresholded/enlarged OCR inputs retain complete readable single digits.
The precise segmentation/model cause remains a hypothesis. No engine or crop changed.
The report contains exact next real-OCR RED fixtures. Full new-code historical
event recall remains `not_evaluated`; old 0/5 recall is not transferred.

## Integrity and independence

`reports/preservation-before.json` records 128 verified prior files plus source
hash/size checks. A6 annotations, approvals, author attribution, lineage and old
reservation remain authoritative. Run-010 development crop review is separate agent
evidence over 44 selected chronological frames, not a new holdout or population sample.
`preservation-after.json` confirms the same 128 prior files and source sizes/hashes
remain intact. No acceptance threshold changed. Optional regression R is deferred
and B is blocked.

## New six-check gate and remaining evidence

`reports/gate-a-final.json` is **fail**, coaching ineligible. It adds the reviewed
numerical outliers to the preserved initial `gate-a.json`. Its six checks are:

| Check | New-code result and scope |
| --- | --- |
| software_regressions | pass, 24 focused capture + 298 full-suite tests |
| lap_events | not_evaluated, no full historical replay under the new fingerprint |
| field_accuracy | fail, two extra reviewed wrong speeds and unresolved HUD contract; fixed-point metrics pass |
| field_coverage | pass, fixed BMW/crash segments only |
| timebase | pass, two new full development artifacts only |
| holdout | not_evaluated, no new distinct reserved recording |

Unannotated pedal latencies remain `not_evaluated`. E16, release-start exclusions,
first-visible-brake semantics and unannotated nearby candidates retain the frozen
A7 restrictions. No old source result is transferred to the new fingerprint.

BMW measurement fingerprint:
`8aceb8b247b477dad3de5c8c862af590efeee1f60bde43336642b3ef1d362b2e`.
Crash measurement fingerprint:
`bcc473fbd75f742e08b56ce30304d7c094f9ce2c975e39ca50109e442be724cb`.
Gate fingerprint:
`7120555640e848989484cd9f681bf10748d13cecb2cdc8c4241e5e9e677fe48a`.
Gate file SHA-256:
`2b95f3ed7befda0bbcbfe6b8c6c333b16c523babe0edc94a121be55c6059a868`.
Per-source reports, manifests and gate contain evidence hashes and absolute paths.

`reports/independent-acceptance-dossier.json` specifies the next prerequisites and
future independent recording reservation. No human input is required to continue
the current development diagnostics. Finish HUD/historical corrections, freeze
their code/config, then reserve a distinct recording before inspecting it. The
already known run-008 holdout remains historical; its reservation is untouched.
