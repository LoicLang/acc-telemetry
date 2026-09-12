---
summary: complete incidents fixed-ROI counter annotations and run-022 measurements against the compatible counter-only extraction
read_when:
  - interpreting incidents counter completeness or comparing full-pipeline replay
  - resuming Gate A after the BMW and incidents numeric-counter reviews
---

# Incidents counter result — run-022

The primary agent reviewed **24,267 distinct raw RGB counter states** on127 sheets.
Exact byte mapping covers all **29,402 native source frames**. All reviewed states are
readable; no unknown/absent state remains in this fixed ROI. This is manual unique-state
review plus exact mapping, not a claim of manual review of all307 original sheets.
No failed Sol/Astra ledger was imported, and no user approval is implied.

The unchanged counter-only extraction agrees on **29,402/29,402 observations**, with
zero missing, wrong or non-observed values. All four numeric changes are detected,
with no missed, duplicate or extra event. Scoped precision and recall are1.0.

| Change | Last old → first new frame | First new digit (s) |
| --- | --- | --- |
| 3→4 | 14→15 | 0.250000 |
| 4→5 | 8780→8781 | 146.350000 |
| 5→6 | 17687→17688 | 294.800000 |
| 6→7 | 28358→28359 | 472.650000 |

The complete ordered mapped sequence contains no other numeric change or reset.
Initial/final lap fragments remain partial; no boundary outside the video is inferred.
Literal frame counts:3=15,4=8766,5=8907,6=10671,7=1043, totaling29402.

P95 midpoint error is **0.008333s**, equal to the half-width of each one-frame bracket.
Each first candidate is exactly the first image showing the new digit. Confirmation
follows **0.066667s** later. Existing1.0s association and0.10s error targets are unchanged;
`fixed_roi_event_status` passes for this counter-only measurement.

## What was checked

Private evidence lives under ignored `data/lab/coaching-reliability/run-022/`.
`prepare.py` verifies the source identity and existing1080p60 preflight, configured
`lap_number_training` ROI `(270,105,58,60)`, every source crop hash, every member's raw
RGB equality with its representative, ordered frame coverage and all rendered tiles.
127 sheets use16 columns, up to12 rows,2× nearest display enlargement, no filtering.
No new video decode or OCR was needed. No application ROI or threshold changed.

`reports/root-review.jsonl` preserves the actual per-sheet labels and reviewer identity.
`evaluate.py` rechecks all24,267 tiles and29,402 source ROI mappings, then writes a new
source-bound per-frame ledger retaining PTS, group, representative, literal and reviewer.
It derives transitions from that ordered ledger, rather than selecting machine events
as annotation windows. Every state was reviewed before the result was calculated.

Compatible input is run-017 `reports/crash-full-counter.json` and its bound reads/freeze.
Source SHA/size, code modules, resolved configuration and OCR asset hashes still match.
`verify_results.py` separately checks ordered labels, transition values and first-new-digit
times, and verifies that the11 files frozen by run-021 remain unchanged.

Reports: `crash-numeric-truth.json`, `crash-results.json`, `result-audit.json`,
`preparation-audit.json`, `final-integrity.json`; labels:
`processed/crash-fixed-roi-labels.jsonl`. Reproduction scripts create outputs exclusively;
use a new run directory rather than overwriting frozen results.

## Scope and remaining work

This uses `LapDetector.observe_lap_number` plus `LapTransitionConfirmer`, **not a full
telemetry-v2 artifact**. That isolated observer leaves `last_observed_time_s` null;
the per-frame calls and input ordering establish the counter-path scope, not normalized
artifact freshness. The earlier40-frame pipeline comparison remains a separate smoke
check; do not turn it into whole-source pipeline parity. Full-pipeline replay is next.

The original L2 timer-reset approval remains10→11. Numeric counter3→4 occurs14→15,
four displayed frames later. Neither channel proves physical line-crossing time.

Together with BMW run-021, fixed numeric ROI reviews now cover76,991 frames across
these two known development sources. This is not independent or other-circuit evidence.
No full-scene visibility, speed accuracy, pedal accuracy or spatial precision follows.
**Overall Gate A remains FAIL; B/R remain blocked.** Speed coverage/numerical truth,
independent recording validation and other previously documented checks remain open.

The complete shared-pipeline trial is now delivered in run-023; see
[real-system-trial-results.md](real-system-trial-results.md). All29402 fresh counter
observations and4/4 events match this frozen truth. The next step is reservation of a
distinct independent capture before inspection, not another counter review.
