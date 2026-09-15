---
summary: video data acquisition first; code audit complete and agent-navigable session platform deferred until the data foundation exists
read_when:
  - starting repository work or choosing the exact next action
  - checking current extraction capabilities, evidence and platform boundaries
---

# Current status

Last verified: **2026-09-15**. Integration branch: `main`.
The owner authorized merging `codex/coaching-reliability` into main for this delivery;
the integration was a fast-forward. Start the next increment on a new `codex/` branch
from current main. No sub-agents, exhaustive counter review or threshold campaign.
Use proportionate checks from AGENTS.md; no OCR replay to change downstream data/docs.

## Vision and priority

**Final product: a persistent driving-data platform that an AI agent can navigate.**
It will expose session summaries, trajectories, references, comparisons, recurrences
and evidence through tools/MCP, with optional skills for investigation. Human reports
are optional views. The agent analyses driving; our software supplies traceable facts.

**Current work: recover and qualify the useful data from video first.** The owner
explicitly deferred platform implementation and agent navigation until the data
foundation exists. Existing local artifacts are sufficient for the next increments.
PC video+telemetry may support spatial labels; future direct PC acquisition should
reuse the same normalized concepts. No MCP server, new database or navigation skill
is implemented or required for the next task.

Active plan: `plans/video-to-agent-platform.md`.
[Code audit](video-data-audit.md) maps all72 catalogue entries to actual code.
[Research catalogue](driving-metrics.md) defines the target and its input requirements.
[Architecture](architecture.md) describes the existing pipeline and future boundaries.

## What the code actually provides

- Native1080p60 CFR preflight, source frames/time, immutable-source artifacts.
- Fresh speed, brake/throttle percentages, gear, confirmed HUD lap number/events.
- Estimated normalized progress `s`/`s_fused` in0–1; `track_position` in percent.
- A HUD steering-dot candidate in−1…1, **not a calibrated physical steering angle**.
- Neutral pedal on/off and gear-change candidates; missing-data intervals and coverage.
- Diagnostic position alignment/delta, coarse per-lap summaries, manual-landmark
  time intervals, annotation-based accuracy/event metrics.

Not delivered: general braking/throttle episode summaries, automatic physical corner
landmarks, metric `s_m/d_m`, trajectory/orientation, dynamics or recurring-loss analysis.
TC/ABS remain missing in modern extraction. `lap_time_s` is empty in run-024 despite
a legacy OCR method existing. Context/incident scene descriptions were manually supplied.
Detailed caveats and code links are in the audit.

**Gate A: FAIL; `coaching_eligible=false`.** Availability is not accuracy. Full throttle
can read about94 %, small pedal residues remain, and some real impact speeds abstain.
No smoothing or invented visibility. Hidden physical quantities require a justified
estimator/other source or remain unavailable; the72-entry catalogue is not a promise
that every channel can be reconstructed exactly from arbitrary video.

## Reusable evidence and actual outputs

All run paths below are relative to ignored `data/lab/coaching-reliability/`.

- run-024 `processed/crash-session/`: 29,402 samples, hashes/envelopes rechecked by
  `read_session_artifacts()` during the audit. Speed29,298; each pedal29,402;
  gear28,913; progress26,844; physical steering/TC/ABS unqualified.
- Source: `data/lab/2026-09-03-generic-s-fusion/crash-representative.mov`,453613415 bytes,
  SHA-256 `b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124`.
- run-021/run-022: finished BMW/incidents counter truth; reuse, no exhaustive reread.
- run-026 `reports/session_coaching.md`: three reviewed passages; retained/reproducible
  via [its implemented contract](specs/2026-09-13-session-coaching-report.md).
- run-027 `reports/lap-4/index.html`: actual full-lap viewer,14 manually routed zones,
  95 neutral candidates and frame-synchronized video. [Commands](perception-package.md).
  Local preview was started on8767; check availability before claiming it is running.
- run-028 `reports/Passage_ACC_pour_analyse_IA.pdf`:17 pages/18 s,59 distinct images.
  External response and evaluation are in `reports/reponse_externe.txt` and
  `evaluation_reponse_externe.md`; frozen reference in `interim/reference_avant_reponse.md`.
  Reconstruction locally favorable, not proof of scalable condensation or coaching.

The audit ran existing event functions across all run-024 samples:316 candidates
(44 brake on/off pairs of counts,46 throttle on/off counts each,135 gear changes and
one initial active-throttle state). Episode pairing is **not** thereby implemented.
Existing tests were read/reused; source videos were not decoded again for this audit.

## Demonstrated issues to account for in the next increment

- Do not treat normalized `s` as metres or minimap centerline as actual trajectory.
- `generate_summary()` counts five HUD numbers where only three laps have both bounds.
- Its all-missing speed aggregate still returns0.0; reproduced in memory. Correct it
  before reusing that aggregate, preserving nulls and field quality.
- Coarse statistics do not distinguish clean/partial/incident laps or qualify phases.

## Exact next action

**Implement phase1A: assemble bounded brake/throttle episodes from run-024 artifacts,
then publish initial temporal descriptors with missing/truncated states and evidence.**
Reuse `analysis/perception.py`; preserve input samples. Start with duration, peak and
release/pickup chronology on existing annotated windows. Avoid spatial claims until
`s_m/d_m` and landmarks are established. No new OCR or platform/MCP work for this step.

For subsequent spatial work, ACC-on-Mac software/service and usable duration are still
unknown. Prepare collection before consuming a limited PC window. Dataset/model work
must demonstrate synchronization, geometry and transfer; none has been launched.
