---
summary: living A7 handoff, failed initial independent measurements, completed reviews and active reviewed-visibility replays
read_when:
  - starting any task
  - resuming reliability validation or changing stage-gate status
---

# Current status

Last verified: 2026-09-08. Branch `codex/coaching-reliability`; A6 checkpoint
`f060637`. Work directly without subagents. Push is authorized; no merge to main.
The user requests autonomous visual verification wherever reliable. Do not repeat
accepted A6 reviews or require the user to verify clear evidence the agent can review.

**A0–A6 complete. A7 validator implemented; independent Gate A fails. B blocked;
C remains separate/inactive.** The three replays consuming newly reviewed control
visibility are currently running. No extraction module or extraction setting changed.

Active specification: `specs/2026-09-05-reference-corner-coach-design.md`.
Active plan: `plans/2026-09-05-coaching-reliability.md`.
Measurement contract: `capture-validation.md`. A6 constraints: `coaching-reliability-resume.md`.

## Stable implementation baseline

Generic progress implementation and representative validation complete; technical
ACC Tasks 1-10 complete. These historical internal-consistency checks do not validate
independent Gate A. Design: `docs/specs/2026-09-03-generic-s-fusion-design.md`.
Boundary-anchor plan: `docs/plans/2026-09-05-generic-boundary-visual-anchor.md`.
Earlier milestone record — Last completed implementation plan: `docs/plans/2026-09-04-temporal-centerline-selection.md`.

## Preserved inputs and new reviews

All run paths below are relative to ignored `data/lab/coaching-reliability/`.
Authoritative A6 index remains `run-007/processed/accepted-corpus-v4/index.json`,
acceptance `run-007/reports/a6-acceptance.json`. Its 100 readable labels per field,
20 degraded frames, 20 typed windows, six physical passages, original recording IDs,
approvals and holdout are unchanged. `run-008/reports/input-integrity.json` verifies
source bytes, prior approval/label/image hashes and reservation compatibility.
All original validation targets are unchanged; three A7 measurement definitions
were added before results, as documented in `capture-validation.md`.

- User approved **only H01–H05**, the five historical counter increments. Exact
  response and displayed-image provenance: `run-008/reports/user-historical-approval.json`.
- Agent subsequently inspected temporal extrema over all 56,246 historical counter
  images and confirmed no additional changes; S01–S04 stay at 1. The opening timed
  lap without an increment is excluded by the operational counter-event definition.
  Separate proof: `run-008/reports/agent-historical-review.json`.
  Current historical truth: `run-008/processed/historical-approved-v2/labels.json`.
- Agent reviewed 109 short brake/throttle intervals (5,463 images / 91.05 s), using
  first/last and all-frame temporal min/max native HUD sheets. Fixed HUD remains
  readable; this qualitative review is not numeric accuracy or a calibrated probability.
  Proof: `run-008/reports/agent-visibility-review.json`. Current derived labels:
  `run-008/processed/agent-reviewed-corpus-v2/`; A6 labels stay untouched. Target
  segments define availability denominators, never implicit visibility for other gaps.
- E16 remains full throttle at frame **30397**; approximate initial 60% is context
  only. E16 and two `first_visible_brake` markers are excluded from 5% crossing
  latency. Applicable truth totals 23 events in 19 windows, with subtype reports.
- Six physical intervals support normalized `s` dispersion only, never meters.
  Automatic blips and E17 steering causality retain their original limitations.

## Confirmed measurements and active work

Initial five full replays and independent timebase checks completed: historical
56,246 frames; clean 18,902; crash 29,402; BMW 47,589; holdout 53,700.
Artifacts: `run-008/processed/{historical,clean,crash,bmw,holdout}-session/`.
Initial results: `run-008/reports/evaluation-v2/`, initial `run-008/reports/gate-a.json`.
That initial gate predates the new historical/visibility reviews; do not treat its
pending lap/coverage statuses as the final result.

| Source | Fresh speed / labels | MAE km/h | P95 km/h |
| --- | ---: | ---: | ---: |
| BMW | 19 / 19 | 2.315789 | 9.0 |
| Crash | 20 / 21 | 1.7 | 6.0 |
| Holdout | 58 / 60 | 1.551724 | 5.15 |

Speed fails unchanged MAE 2 / P95 5 targets; holdout also has six fresh readings
on 20 approved absent-HUD frames. Historical replay emits **0 events for 5 approved
transitions**; current raw OCR initially reads 7 where the reviewed image shows 0,
and later sustained 20/30. This is a confirmed extraction failure, not a missing
human approval. Do not tune extraction on holdout to fix it.

Initial landmark circular ranges: BMW 0.000120233 (2/2), crash 0.001578158 (2/2),
holdout unavailable (0/2, unanchored). These are dispersion, not spatial error.
Initial pedals were absent because visibility spans were empty. Replays with the
new visibility evidence now write `*-reviewed-session/`; logs are
`run-008/reports/{bmw,crash,holdout}-reviewed-extraction.log`. This rerun consumes
new evidence without changing extraction parameters. The validator itself never
reruns OCR.

## Verification and exact next action

22 focused capture tests, 9 diagnostic tests and 286 full-suite tests pass for
the validator commit. RED logs and reproducible local review/run scripts are
preserved under `run-008/`. Generated/private data is ignored.

**Next action:** finish the three active reviewed-visibility artifact jobs, validate
these against `agent-reviewed-corpus-v2` and historical artifacts against
`historical-approved-v2`, then publish a new final gate with fresh test evidence,
update this handoff/plan and commit/push the results. Do not start B.
