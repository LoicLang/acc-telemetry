---
summary: authoritative handoff for A6 corpus completion, verified lineage, remaining human review and blocked A7
read_when:
  - starting any task
  - resuming work after another agent
  - changing project priorities or milestone status
---

# Current status

Last verified: 2026-09-07. This is the single living handoff. Recent Git history is
canonical for commit IDs. Earlier detailed status is preserved in
`archive/2026-09-07-status-before-a6-lineage.md`; do not load it for routine resumption.

## Objective and branch

Build reliable ACC PS5 video telemetry before a reference-based corner coaching
dossier. A0–A5 and A6 software are complete. **A6 corpus acceptance is pending;
A7 has not started. Gate A is unvalidated, B blocked, C separate and inactive.**

- Branch: `codex/coaching-reliability`, tracking the same branch on origin.
- Starting checkpoint for this handoff: `d2581e8`, already pushed.
- Latest user direction: prioritize a clean, concise, executable repository handoff
  for a less powerful agent because token quota is low; defer further implementation.
- Push authorized. No merge to main requested. Raw media must remain immutable.
- Active specification: `specs/2026-09-05-reference-corner-coach-design.md`.
- Active plan: `plans/2026-09-05-coaching-reliability.md`.
- **Read next:** `coaching-reliability-resume.md`, the concrete remaining-work guide.
- Downstream: `plans/2026-09-05-reference-corner-dossier.md` (blocked);
  `plans/2026-09-05-replay-spatial-feasibility.md` (inactive).

## Stable implementation baseline

Generic progress and boundary visual-anchor implementation and representative validation complete.
Technical ACC Tasks 1-10 complete. These software/replay results do not validate the
independent coaching gate. Design reference: `docs/specs/2026-09-03-generic-s-fusion-design.md`.
Latest completed implementation plan: `docs/plans/2026-09-05-generic-boundary-visual-anchor.md`.
Earlier milestone record — Last completed implementation plan: `docs/plans/2026-09-04-temporal-centerline-selection.md`.

## Authoritative local corpus

Latest: `data/lab/coaching-reliability/run-005/processed/accepted-corpus-v3/index.json`.
Its source labels/review reports were validated with the current annotation validator.
It derives from `run-004/processed/accepted-corpus-v2/`, changing **only development
recording IDs** in labels. Frames, values, visibility, events, context and roles are
unchanged. All original approval snapshots and v2 remain untouched.

| A6 criterion | Verified result |
| --- | --- |
| Readable speed / brake / throttle | 100 each, accepted; do not re-review |
| Degraded/menu cases | 20, accepted; do not re-review |
| Timed pedal-event windows | 19 / 20; one more required |
| Development lineage | Resolved locally; readiness check passes |
| Physical passages | 0 reviewed per source; two per source required by current config |
| Distinct recordings / roles | Three recordings: two development, one reserved holdout |
| Overall readiness | `not_evaluated`; only `events` and `repeated_passages` false |

### Provenance resolved in this handoff

`run-005/reports/development-lineage.json` contains freshly computed file identities:

- BMW is the original `/Users/loiclang/Movies/2026-09-03 22-42-08.mov`;
  SHA-256 `76859897055ddbac6bb52f6299dc7b86a6daf36bb3182b8d64d3da6c9aae378d`.
- Incident clip `data/lab/2026-09-03-generic-s-fusion/crash-representative.mov`
  derives from `/Users/loiclang/Movies/2026-09-02 22-40-01.mov`, original SHA-256
  `ee3d83027a72b0c546cd4a773179a070e25b9c1d6002fa43bebd30f812705678`.
  All 29,416 compressed video packet SHA-256 hashes match a contiguous original
  sequence; PTS offset is exactly +515 seconds with zero offset spread.
- Holdout retains original recording ID
  `a29ae2705f89d13f6c2247ef31c919b8f3516a6a016a6aaffa700ac378bf1aed`.
  Its 895-second lossless prefix and tail exclusion are documented in
  `capture-annotations.md` and `run-004/reports/holdout-lossless-transform.json`.

Local scripts `run-005/resolve_lineage.py` and `run-005/apply_lineage.py` preserve the
verification/migration method. Outputs and personal evidence are ignored by Git.
No extraction code, thresholds or production configuration changed.

## Human evidence constraints

- Accepted approvals: `run-002/reports/approval.json`, `run-003/reports/approval.json`,
  `run-004/reports/approval.json`, under `data/lab/coaching-reliability/`.
- E01/E12/E16 contain descriptions without precise timestamps. Do not invent times.
- E17 “too much steering” is the pilot's hypothesis, not an established cause.
- User-reported downshift throttle spikes are automatic. Preserve HUD readings;
  do not interpret these as voluntary throttle reapplication or a driving mistake.
- Throttle release, brake onset, timer reset, numeric lap-counter update and physical
  crossing are distinct. Existing L1/L2/L3 markers do not approve physical landmarks.
- Review convention: uncorrected **displayed** proposals are accepted when the user
  responds to that batch. Silence, unseen frames and prepared images are not approval.
- Holdout was reserved before inspection at `92e4223`. Do not tune extraction on it.

## Verification and exact next action

263 full-suite tests pass; focused annotation/consolidation tests and docs discovery
pass. See `run-005/reports/` for logs. v3 preserves every label except the two
recording IDs and passes structural validation; source roles and counts are unchanged.
No raw media was changed. Documentation is the only tracked change in this handoff.

**Next action:** follow `coaching-reliability-resume.md` step 1 to prepare one small
human review containing a twentieth timed pedal event and six physical-passage
intervals (two per source). That focused package has **not** been created yet.
The existing full review portal remains `run-004/reports/START_HERE.html`.
Obtain scoped human review before completing A6 or executing A7. Do not repeat H/M.
