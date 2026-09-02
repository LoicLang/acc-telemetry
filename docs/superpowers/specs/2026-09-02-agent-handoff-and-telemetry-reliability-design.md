# Agent Handoff and Telemetry Reliability Design

## Purpose

Make the repository sufficient context for a new agent to resume work without relying on a previous chat. The documentation must say what is true now, what evidence supports it, what is currently being worked on, what comes next, and which work is blocked.

The immediate technical objective is to restore confidence in the longitudinal coordinate `s`, lap transitions, and quality propagation before any corner segmentation or coaching score is implemented.

## Documentation model

The active documentation has four distinct responsibilities:

1. `AGENTS.md` defines permanent repository rules and the required handoff protocol.
2. `docs/current-status.md` is the single living entry point for the current state of the project.
3. `docs/acc-ps5-plan.md` explains the durable ACC PS5 product direction and stage gates.
4. A dated implementation plan under `docs/superpowers/plans/` defines the exact test-driven tasks and atomic commits for the active milestone.

These files must link to one another. A new agent starts with `AGENTS.md`, then reads `docs/current-status.md`, then follows the active implementation plan.

Historical reports remain under `docs/legacy/` and must not be treated as current truth.

## Required handoff protocol

Every agent that changes code, tests, configuration, data-processing behavior, or active documentation must leave the repository in a resumable state.

Before starting work, the agent must:

- read `AGENTS.md` and `docs/current-status.md`;
- inspect `git status`, recent commits, and the active plan;
- verify that any referenced local evidence exists before relying on it;
- preserve unrelated user changes.

During work, the agent must:

- execute one coherent task at a time;
- use a focused failing test before changing behavior;
- keep the active plan checkboxes and `docs/current-status.md` synchronized with verified facts;
- record evidence and distinguish confirmed facts from hypotheses;
- avoid implementing downstream coaching features while a prerequisite stage gate is failing.

Before stopping, the agent must:

- run the focused tests and the full test suite appropriate to the change;
- update `docs/current-status.md` with completed work, current work, blockers, evidence, and the exact next action;
- update the durable plan only when product direction or a stage gate changes;
- make atomic commits with descriptive messages;
- leave no unexplained tracked changes.

The documentation update belongs in the same commit as the behavior whose status it describes when separating them would make either commit misleading. A standalone documentation decision or planning change receives its own documentation-only commit.

## Current verified state

The 1280x720, 60 FPS ACC PS5 capture path is usable. Controls, speed, gears, static full-map extraction, and real lap transitions have produced useful observations.

The longitudinal coordinate `s` is not reliable enough for corner segmentation or lap alignment:

- the controlled Spa capture of 2026-09-01 reaches `s >= 99.9%` at 88.033333 seconds in a 180-second capture;
- `s` remains at or above 99.9% for 50.027742% of frames;
- after the real lap transition at 178.2 seconds, the new-lap reset produces a plausible restart near zero;
- the longer Spa session reproduces the initial-anchor failure;
- the longer session also exposes false lap transitions caused by lap-number OCR;
- lap-time OCR is missing, but it is not the first blocker for position-aligned coaching.

The quality-aware `TelemetrySample` contract exists, but the active pipeline and exported session CSV files still use legacy records without field-level quality and anomaly output. Therefore quality is modeled but not yet propagated through the real coaching data path.

## Failure mechanism and uncertainty

The observed saturation is consistent with the current control flow:

1. path extraction installs a geometrically estimated start index;
2. the tracker does not capture the current red-dot position as a new start until a lap transition calls `reset_for_new_lap()`;
3. travel direction is inferred from the shorter arc away from the current start index;
4. backward measurements are held by the monotonic validator;
5. once the previous position is above 90%, a large drop is converted to 100%, which can keep the signal saturated until a trusted reset.

This mechanism explains why a bad initial anchor can become a long plateau. It does not yet prove which geometric or detection error first selects the bad position. The implementation work must add diagnostics and a real-data regression test before choosing the production fix.

False lap-number transitions are a separate upstream risk because each accepted transition resets the position anchor. They require evidence-based confirmation rules rather than a position-layer workaround.

## Stage gates and priority order

### Priority 1: trustworthy `s` anchor and progression

Add a reproducible regression from the 2026-09-01 Spa evidence, expose the raw projection and validator decisions needed for diagnosis, correct the root cause, and re-run the controlled capture.

Exit criteria:

- `s` does not reach the completion band before the real start/finish crossing;
- `s` restarts near zero only at a confirmed new lap;
- progress is monotonic within an explicitly documented tolerance without hiding long invalid plateaus;
- the same known track passages map to stable `s` ranges across repeated laps;
- low-confidence or unavailable position is represented explicitly rather than silently held as observed truth.

### Priority 2: robust lap transitions

Separate raw lap-number OCR observations from confirmed lap transitions. Require temporal stability and transition plausibility before updating lap state or resetting the position tracker.

Exit criteria:

- isolated OCR changes do not create a transition;
- one real increment creates exactly one transition;
- missing or implausible readings preserve the last confirmed lap with degraded quality;
- the long 2026-09-01 capture produces no false position resets;
- existing short-video and API behavior remains covered.

### Priority 3: quality propagated end to end

Connect extraction observations to normalization and the domain contract, then expose field-level quality and anomalies in the outputs consumed by analysis. Preserve legacy compatibility deliberately rather than treating legacy dictionaries as normalized telemetry.

Exit criteria:

- the application pipeline provides normalized `TelemetrySample` data or an equally explicit typed result at its analysis boundary;
- `s`, lap number, speed, controls, and other relevant fields carry their own quality state;
- held values are distinguishable from observed values;
- anomaly reasons survive into a machine-readable output used by analysis;
- existing CSV/API consumers either receive a versioned extension or remain supported by an explicit compatibility adapter.

### Downstream gate

Corner segmentation, driving-event extraction, lap/reference comparison, coaching rules, dashboards, and generative feedback remain blocked until all three priorities above meet their exit criteria on the controlled Spa session.

Afterward, the first coaching milestone is one manually reviewed Spa corner segment, not a complete circuit model.

## Planned commit boundaries

Documentation setup uses separate atomic commits:

1. record this design decision;
2. establish the handoff rules and current-status entry point;
3. align the durable ACC PS5 plan with the failed 2026-09-01 validation;
4. add the detailed implementation plan for the three reliability priorities.

Implementation will use one or more commits per priority, with each commit independently tested and limited to a coherent behavior change. Diagnostic instrumentation, production correction, quality propagation, and documentation updates must not be bundled unless they are inseparable for repository truthfulness.

## Non-goals

- no corner catalogue or automatic corner detection;
- no lap-reference comparison based on the current `s` signal;
- no coaching score, dashboard, LLM coach, or lateral `d` work;
- no deletion or modification of immutable raw captures;
- no commit of personal video, full local telemetry exports, or generated reports;
- no attempt to solve the failure by tuning thresholds without first reproducing and tracing it.
