---
summary: living A8 handoff for fresh speed correction, development revalidation and remaining Gate A blockers
read_when:
  - starting any task
  - resuming reliability corrections or changing stage-gate status
---

# Current status

Last verified: **2026-09-09**. Branch `codex/coaching-reliability`; A6 checkpoint
`f060637`, A7 validator introduced by `006629f`. Recent Git history owns later IDs.
Delegate only with an explicitly selected model below GPT-6 Astra, proportionate
to complexity. Push is authorized; no merge to main. The user
explicitly requests autonomous visual verification wherever reliable, with uncertainty
preserved; do not ask them to repeat accepted or reliably agent-verifiable reviews.

**A0–A7 implementation/evaluation complete. Gate A FAILS; B blocked. C remains
separate/inactive.** A8 changes modern speed extraction; acceptance targets remain
unchanged. Full BMW/crash development replays finished; measurement publication remains.

Active correction specification: `signal-treatment.md`.
Active plan: `plans/2026-09-09-fresh-measurements.md` (**S1/S2 implemented; S3–S5 being finalized**).
Parent product specification: `specs/2026-09-05-reference-corner-coach-design.md`.
Completed A7 execution: `plans/2026-09-05-coaching-reliability.md`; Gate A still fails.
Contract: `capture-validation.md`. Full results: `capture-validation-results.md`.
Preserved semantic constraints: `coaching-reliability-resume.md`.

## Current implementation

Real extraction/pipeline RED tests reproduced 246→255, 179→188 and held invalids.
Modern speed now publishes strict fresh OCR values or explicit absence, retaining
raw text and reasons. Legacy median/holding stays isolated in `extract_speed`.
No temporal speed heuristic, pedal smoothing or regression R was added. S3 found
a separate CSV/API timestamp precision defect, being committed separately.
New evidence: `fresh-measurement-results.md`, ignored run-010. HUD validity and
historical OCR remain separate A blockers; B and R must not start.

New confirmed development evidence: **40/40 raw OCR speed readings are exact** on
the selected 19 BMW + 21 crash labels. Subsequent median-filtered outputs include
246→255 and 179→188. Scope is these points only, not all frames. Read-only proof with
input hashes: `data/lab/coaching-reliability/run-009/reports/speed-raw-vs-output.json`.
The benefit of a regression curve remains a hypothesis; no model was tested or added.

## Stable implementation baseline

Generic progress implementation and representative validation complete; technical
ACC Tasks 1-10 complete. Those historical internal-consistency checks do not validate
independent Gate A. Design: `docs/specs/2026-09-03-generic-s-fusion-design.md`.
Boundary-anchor plan: `docs/plans/2026-09-05-generic-boundary-visual-anchor.md`.
Earlier milestone record — Last completed implementation plan: `docs/plans/2026-09-04-temporal-centerline-selection.md`.

## Frozen A7 authority (old fingerprint only)

All run paths below are relative to ignored `data/lab/coaching-reliability/`.
A6 remains accepted and unchanged: `run-007/processed/accepted-corpus-v4/index.json`,
proof `run-007/reports/a6-acceptance.json`. Original labels, approvals, six physical
intervals, recording IDs, roles and holdout reservation remain intact.

**Frozen final A7 gate:** `run-008/reports/evaluation-final-v2/gate-a.json`.
These results are not transferred to the changed A8 extraction fingerprint.
Human-readable report: `run-008/reports/RESULTS_A7.html`.
Earlier `run-008/reports/gate-a.json`, `evaluation-v2/` and `evaluation-final/`
are superseded diagnostic snapshots. Do not use their old pending statuses or
unqualified release offsets as final acceptance results.

| Gate check | Final result |
| --- | --- |
| software_regressions | pass: 24 capture + 9 diagnostic; 288 full-suite tests |
| lap_events | fail: 0/5 approved historical counter increments detected |
| field_accuracy | fail: speed exceeds targets; holdout has 6 fresh readings on 20 absent-HUD labels |
| field_coverage | pass, only 109 fixed short segments / 5,463 frames / 91.05 s |
| timebase | pass, all five full source artifacts and independent capture checks |
| holdout | fail; original extractor/settings reservation remains compatible |

Speed MAE/P95 km/h: BMW **2.315789/9** (19/19 fresh labels), crash **1.7/6**
(20/21), holdout **1.551724/5.15** (58/60). Brake and throttle MAEs pass 5 points,
with 100/100 readings per field. Scoped speed availability is 100%, 96.1933%,
99.0275%; each pedal is 100% on those segments. This is not whole-lap coverage.

Landmark circular `s` ranges: BMW 0.000120233 (2/2), crash 0.001578158 (2/2),
holdout unavailable (0/2, unanchored). No conversion to meters is justified.

## Reviews, exclusions and provenance

- User approval covers only H01–H05: `run-008/reports/user-historical-approval.json`.
  Agent's separate all-frame counter review confirms exhaustiveness and rejects
  four old suspect increments: `agent-historical-review.json` in the same directory.
- Independent agent visibility review uses first/last and temporal min/max sheets
  incorporating all 5,463 target images: `agent-visibility-review.json`. It is
  qualitative, not a calibrated probability; extrema do not preserve frame order.
  Point approvals were not expanded by implication. Reviewer identity is preserved.
- Current derived labels: `run-008/processed/agent-reviewed-corpus-v2/` and
  `historical-approved-v2/`. Reviewed artifacts: `{bmw,crash,holdout}-reviewed-session/`;
  historical and additional clean artifacts: `{historical,clean}-session/`.
- Final pedal timing: 16 onset/reapplication markers in 15 windows, all on holdout;
  12/12 brake onsets (P95 0.0475 s), 4/4 reapplications (P95 0.00833345 s).
  Two extra nearby crossings are unannotated candidates, not proven false positives.
- E16 remains full throttle at **30397**, approximate initial 60% context only.
  E16, two first-visible-brake markers and seven generic release starts are excluded
  from the 5% latency metric. Release-start images show filled bars; falling release
  latency remains `not_evaluated`. Proof: `pedal-semantics-review.json`. No original
  event was relabelled; these are not B4 detector results. Blips and E17 causality
  retain their original restrictions.

Gate SHA-256: `8b0d323bef702ce8e7dafa4e68c2be2c736f7c06b55d221c4a5ea8f8f6551373`.
Measurement fingerprint: `d9808e44a6abfb24b78e33d14879409b61c7e727fbeaf6bb15dac67afaa50ae3`.
`evaluation-final-v2/integrity.json` and `input-integrity.json` verify preserved A6
and unchanged reserved extraction settings/modules. Three A7 metric-definition
settings were fixed before results; all old acceptance targets remain unchanged.

## Verification and exact next action

288 full-suite tests pass, including the 24 focused capture and 9 diagnostic tests;
RED logs, final tests, docs discovery and local reproduction/review scripts remain
under `run-008/`. Private/generated evidence is ignored. The final validator reads
telemetry-v2 without OCR. The final correction also prevents generic release starts
and sparse extra crossings from being misreported as latency errors/false positives.

Run-010 preserves S1 RED (5 tests, 6 functional failures), S2 GREEN (5 tests),
16 OCR/legacy tests, 91 S3 focused tests and a 298-test passing full suite.
`reports/preservation-before.json` verified 128 prior files and source sizes/hashes
before edits. The old gate/reservation and A6 authorship remain unchanged.
Known holdout run-008 cannot become independent again or receive a rewritten reservation.

**Next action:** finish the separate S3 consumer commit, then publish S4/S5 metrics
and the six-check gate from existing run-010 development artifacts without rerunning OCR.
