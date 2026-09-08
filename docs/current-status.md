---
summary: authoritative handoff for accepted A6 corpus, preserved event semantics and pending A7 reliability evaluation
read_when:
  - starting any task
  - resuming work after another agent
  - changing project priorities or milestone status
---

# Current status

Last verified: 2026-09-08. This is the single living handoff; recent Git history
is canonical for commit IDs. Earlier detail remains in focused documents and local
ignored evidence. Do not load archived status for routine resumption.

## Objective and branch

Build reliable ACC PS5 video telemetry before a reference-based corner coaching
dossier. **A0–A6 are complete, including A6 corpus acceptance. A7 has not started;
Gate A is unvalidated, B blocked, C separate and inactive.**

- Branch: `codex/coaching-reliability`, tracking origin; starting checkpoint `2811276`.
- Latest user direction: finish A6, then revisit the working method before continuing.
  The user subsequently requested direct work without subagents; no new delegation.
- Push authorized. No merge to main requested. Raw media remains immutable.
- Active specification: `specs/2026-09-05-reference-corner-coach-design.md`.
- Active plan: `plans/2026-09-05-coaching-reliability.md`.
- Read next: `coaching-reliability-resume.md` for A7 evidence constraints.
- Downstream dossier plan remains blocked; replay-spatial feasibility is inactive.

## Stable implementation baseline

Generic progress and boundary visual-anchor implementation and representative validation complete.
Technical ACC Tasks 1-10 complete. These software/replay results do not validate the
independent coaching gate. Design reference: `docs/specs/2026-09-03-generic-s-fusion-design.md`.
Latest completed implementation plan: `docs/plans/2026-09-05-generic-boundary-visual-anchor.md`.
Earlier milestone record — Last completed implementation plan: `docs/plans/2026-09-04-temporal-centerline-selection.md`.

## Accepted local corpus

Authoritative index:
`data/lab/coaching-reliability/run-007/processed/accepted-corpus-v4/index.json`.
Fresh `validate_annotations()` reports and `corpus_readiness()` pass against the
unchanged `config/validation.yaml`. A6 certifies input readiness, not accuracy.

| A6 criterion | Verified result |
| --- | --- |
| Readable speed / brake / throttle | 100 each |
| Degraded/menu cases | 20 |
| Timed pedal-event windows | 20, preserving each event type |
| Physical passages | Six reviewed intervals, two per source |
| Recordings / roles / lineage | Three originals, two development and one reserved holdout |
| Overall readiness | All eight checks pass; coaching eligibility remains false |

v4 copies v3 and adds only six physical passages, the E16 full-throttle marker and
its scoped context. All prior labels, context, visibility, roles and recording IDs
are unchanged. Empty continuous visibility spans remain empty. Old approval files,
v3 and the displayed run-006 proposal snapshot remain untouched.

`run-007/reports/approval.json` stores the exact user response, approved definitions,
frame/image/source identities and scope. `a6-acceptance.json` records fresh reports,
configuration hash and verified unchanged prior files. `run-007/accept_review.py`
preserves the one-time migration method; do not rerun over existing outputs.
All run paths in this document are under ignored `data/lab/coaching-reliability/`.

## Accepted semantics and remaining limitations

- The user approved all six displayed physical intervals. They track the near/lower
  edge of the transverse checker stripe at fixed image x=960, y=580 (BMW) or y=600
  (McLaren). They support repeated-passage dispersion, not metric position accuracy
  or the instant an axle crosses the line.
- E16: user reports roughly 60% throttle at the start and reaching 100% at frame
  **30397 (506.616667 s)**. Type is `throttle_reaches_full`; the initial estimate
  has no quantitative tolerance and remains context only, outside accuracy labels.
  The frame marker has 1/60 s resolution, with timing uncertainty unknown.
- E16 is **excluded from the A7 5% crossing latency metric**. It completes a generic
  timed pedal window for A6; A7 must publish subtype-specific denominators/exclusions
  and obtain additional applicable truth if needed. Never relabel it as onset from zero.
- E01/E12 remain descriptive without timed markers. Earlier E16 description is kept
  as historical context and explicitly supplemented by the new user response.
- Automatic downshift blips remain displayed readings, not inferred voluntary inputs;
  E17 steering causality remains the user's hypothesis.
- Provenance remains verified in `run-005/reports/development-lineage.json`:
  incident clip packets match the original with +515 s offset; BMW original hash
  matches. Holdout original ID and lossless-prefix proof remain preserved, reserved
  before inspection at `92e4223`; no measurement code/settings were tuned on it.
- A7 still needs historical full-capture transition truth and applicable continuous
  visibility review before claiming continuous coverage. A6 does not supply those.

## Verification and exact next action

263 full-suite tests and 17 focused annotation/consolidation tests pass; docs discovery
and diff check pass. Logs are under `run-007/reports/`. The accepted status page is
`run-007/reports/START_HERE.html`; the prior seven-card viewer is preserved in run-006.
No production code, thresholds, raw media or prior human approval changed.

**Next action:** discuss the working method with the user now that A6 is complete,
as requested. Do not start A7 in this turn. When resumed, A7 begins with the active
plan's RED tests for empty truth, identical bias and one-to-one event matching.
