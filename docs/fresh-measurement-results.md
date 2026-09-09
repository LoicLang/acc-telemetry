---
summary: A8 fresh measurement evidence and distinct unresolved HUD, historical OCR and independent validation work
read_when:
  - assessing A8 implementation and development results
  - resuming separate HUD or historical OCR corrections before Gate A acceptance
---

# A8 fresh measurements — 2026-09-09

Gate A remains blocked. New evidence lives under ignored
`data/lab/coaching-reliability/run-010/`; run-008 and run-009 remain frozen.
S1–S3 are implemented. S4/S5 publication is being finalized.

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

`reports/hud-contract-before.json` is a controlled-backend development probe, not
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
No acceptance threshold changed. Optional regression R is deferred and B is blocked.
