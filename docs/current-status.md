---
summary: single source of truth for current project state, active work, blockers, and exact next action
read_when:
  - starting any task
  - resuming work after another agent
  - changing project priorities or milestone status
---

# Current status

Last verified: 2026-09-02

This document is the mandatory living handoff for the repository. Update it from
verified evidence whenever active work, blockers, stage gates, or the next action
change. Use `git log` for authoritative commit hashes and dates.

## Current objective

Validate native 1080p telemetry input and isolate the first invalid transition in
`s` before selecting a production correction.

- Active milestone: native 1080p baseline and `s` diagnostics
- Status: implementation plan ready; execution authorized
- Active specification: `docs/superpowers/specs/2026-09-02-native-1080-and-s-diagnostics-design.md`
- Active plan: `docs/superpowers/plans/2026-09-02-native-1080-and-s-diagnostics.md`
- Last completed plan: `docs/superpowers/plans/2026-09-02-agent-handoff-documentation.md`
- Technical ACC implementation: limited to the approved profile and diagnostic slice
- Documentation milestone: verified complete

## Resume here

1. Run `./scripts/docs-list`.
2. Read this document.
3. If an active plan is named above, read it before changing that milestone.
4. Inspect `git status --short --branch` and `git log --oneline -10`.
5. Continue from the first unchecked plan step.

## Recently completed

- Repository foundations and package boundaries were completed on 2026-08-31.
- The quality-aware `TelemetrySample` domain contract was added.
- CLI and web processing share `TelemetryPipeline`.
- The agent-handoff and telemetry-reliability design was recorded in commit
  `e870506`.
- Dynamic documentation discovery was added to that design in commit `67167a3`.
- The current documentation implementation plan was recorded in commit `720c3fd`.
- The tested documentation index was implemented in commit `595a6cf`.
- The mandatory handoff protocol and living status were added in commit `a581c19`.
- The ACC PS5 plan was corrected from the 2026-09-01 evidence in commit `457a1e1`.

Verification for the documentation milestone:

- documentation index exits successfully and lists four active documents;
- all 64 repository tests pass;
- Python compilation succeeds for `src`, `scripts`, `tests`, and launchers;
- no telemetry production behavior was changed in this milestone.

## Verified working baseline

- ACC PS5 capture at 1280x720 and constant 60 FPS is usable.
- The static full-map HUD path is extracted.
- Controls, speed, and gears produce useful observations.
- Real lap transitions can be detected on the controlled short capture.
- Raw session videos remain immutable and ignored by Git.

## Confirmed blockers

### Longitudinal coordinate `s`

Status: failed validation; not safe for corner segmentation or lap alignment.

Evidence from the controlled Spa capture on 2026-09-01:

- `s` first reaches at least 99.9% at 88.033333 seconds in a 180-second capture;
- `s` remains at or above 99.9% for 50.027742% of frames;
- the real lap transition occurs around 178.2 seconds;
- after that confirmed transition, the reset produces plausible progress near zero.

The longer Spa session reproduces `initial_s_anchor: fail_reproduced`.

### Lap transitions on long captures

Status: failed validation.

The longer 2026-09-01 session records
`long_capture_lap_number_ocr: fail_false_transitions`. A false confirmed transition
can reset the position anchor, so this is a prerequisite for trustworthy `s` across
multiple laps.

### Quality propagation

Status: modeled but not connected end to end.

`TelemetrySample` supports field-level observed, missing, held, interpolated, and
anomalous states. The active pipeline and session CSV exports still contain legacy
records without field-quality or anomaly output.

## Local evidence

The following evidence is intentionally ignored by Git and may be absent on another
machine:

- `data/sessions/2026/2026-09-01_spa_ps5_capture-test/session.yaml`
- `data/sessions/2026/2026-09-01_spa_ps5_capture-test/processed/telemetry_20260901_182913.csv`
- `data/sessions/2026/2026-09-01_spa_ps5_braking-baseline-aborted/session.yaml`

New immutable external captures for the active milestone:

- `/Users/loiclang/Movies/2026-09-02 21-55-05.mov`: primary clean BMW session,
  1920x1080/60 FPS, 2326.033333 seconds, at least 12 visible laps;
- `/Users/loiclang/Movies/2026-09-02 22-40-01.mov`: secondary robustness session,
  1920x1080/60 FPS, 1137.016667 seconds, recent car change and crashes.

Verify these paths exist before using them. Their summarized findings above are the
durable repository record; personal videos and full telemetry exports must not be
committed.

## Priority order after the review gate

1. Make the initial `s` anchor and progression trustworthy.
2. Confirm lap transitions robustly on long captures.
3. Propagate field-level quality and anomalies through the real pipeline.

Corner segmentation, driving-event extraction, reference comparison, coaching
rules, dashboards, and generative feedback remain blocked until these three gates
pass on controlled Spa evidence.

## Current next action

Execute the active plan task by task with focused tests and atomic commits. Stop after
the 1080p measurement and root-cause diagnostic, before implementing a production
correction for `s`.
