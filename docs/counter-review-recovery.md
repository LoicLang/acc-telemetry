---
summary: run-018 visual-review recovery attempts, rejected sustained annotations and scoped verification of eight counter-event predictions
read_when:
  - resuming exhaustive counter review after failed agent annotations
  - interpreting targeted counter-event measurements or choosing a reliable reviewer
---

# Counter review recovery — 11 September 2026

**The exhaustive visual method is not qualified.** The current gpt-5.6-sol workflow
cannot supply trusted complete-source annotations. All extended review ledgers in
ignored `data/lab/coaching-reliability/run-018/reports/` remain diagnostic only.
No old source, approval, evidence, code or configuration was changed.

## Qualification and sustained failures

The initial recovery protocol displayed exactly one explicitly identified image per
tool result, requesting `original` detail both from `view_image` and the image emitter.
Root and gpt-5.6-sol independently agreed on all **960 cells from 10 selected sheets**,
including four transitions. A second reviewer agreed on its 480-cell qualification.
These tests qualified only their selected cells, not sustained accuracy.

The extended passes failed root native-pixel checks again: BMW frame453 was reported
absent but clearly shows0; incidents frame799 was reported absent but clearly shows4.
Their ledgers are preserved and must not be imported as truth. Earlier run-017 false
absence/unknown annotations remain rejected as well.

A fresh bounded reviewer stopped correctly at a doubtful sheet cell and recovered0
from the native crop. A new compact presentation then retained the existing profile's
native counter ROI `(270,105,58,60)` with2× nearest-neighbour display,12 columns and
one image per result. It was prepared for33 sheets, but the reviewer stopped after
only **102 inspected cells** with uncertainty at BMW101. Root's native check clearly
reads0. The 31 uninspected compact images are not reviewed by implication.

The cause is **not established**. Equal source/file hashes and contradictory readings
do not prove that rendering changed; interpretation, image handling or model perception
remain possible causes. No project OCR defect or new HUD disappearance is inferred.
Further large passes with the same unqualified workflow are not justified.

Proof: `reports/qualification-{root,sol}.json`, `qualification-comparison.json`,
`bmw-v2-rejection.json`, `bmw-bounded-v3/compact-test.json`, `compact-pilot.json` and
`method-outcome.json`. No pilot or failed extended run validates all803 original sheets.

## Trusted targeted event measurements

Root directly reviewed the pixel windows for every currently published counter-event
prediction. The selection comes from prior known/output-located windows; it is **not
an independent exhaustive search for events**. `reports/root-targeted-events.json`
records the exact brackets, source hashes, image hashes, reviewer and selection limits.

| Source | Visible counter increments: last previous → first new frame |
| --- | --- |
| BMW | 17167→17168;25871→25872;34630→34631;43342→43343 |
| Incidents | 14→15;8780→8781;17687→17688;28358→28359 |

All **4/4 BMW and4/4 incidents predictions** match actual displayed numeric increments.
P95 midpoint timing error is approximately **0.008333 s** per source; confirmation
follows the first fresh candidate by approximately0.066667 s. These are numeric-counter
updates, not timer reset or physical line-crossing times. Original L2 timer-reset
approval at10→11 is unchanged and separate from the counter increment at14→15.

BMW reuses the intact, current-code-compatible full run-015 artifact. Incidents reuse
the current counter-only extraction in run-017, whose40-frame smoke matched the actual
pipeline. Source, code, resolved settings, payload and OCR-asset compatibility were
reverified in `reports/reuse-integrity.json`; no new full replay was performed.
The incidents result is still counter-path evidence, not a full telemetry-v2 artifact.

The unchanged event matcher uses the1.0s association window and0.10s P95 acceptance
target. `reports/targeted-event-results.json` explicitly sets complete review false,
**recall not_evaluated and lap-event gate not_evaluated**. No event was found false
among the eight reported predictions, but additional missed events elsewhere cannot
be ruled out. There is no new all-frame counter accuracy, speed, pedal or spatial claim.

## Handoff

**Gate A remains FAIL; B and R remain blocked.** Independent acceptance and other
previous coverage/field-quality limitations remain unchanged. No holdout or720p work.
No background job remains active. Focused/full tests, docs discovery, diff check and
saved-evidence checks are recorded under `run-018/reports/`.

The owner originally prohibited Astra sub-agents and limited visual delegation to
explicitly selected gpt-5.6-sol. They subsequently authorized a bounded Astra visual
experiment. Its result and limits are in [astra-review-trial.md](astra-review-trial.md).
The older failures above remain preserved and unaccepted; the new trial does not
retroactively qualify them or establish complete-source truth.
