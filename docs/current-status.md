---
summary: run-033 fixes HUD fragment contamination and supplies the active calibrated session and episodes
read_when:
  - starting repository work or choosing the exact next action
  - checking current extraction capabilities, evidence and platform boundaries
---

# Current status

Last verified: **2026-09-15**. Branch: `codex/video-control-episodes`, created from
main at `6b2c04b`. **Active data baseline: run-033.** No sub-agents, threshold campaign
or OCR replay. The duplicate plan was removed; the plan linked below is authoritative.

## Product and active scope

Build a persistent driving-data platform navigable by an AI agent: observations,
trajectories, references, comparisons and evidence. The software supplies facts;
the consuming agent analyses driving. Human reports are optional views.

Recover and qualify useful video data first. Platform/database/MCP and navigation
skills remain deferred. PC video+telemetry may support spatial labels; direct PC
acquisition is a future adapter. Do not present hidden physical quantities as video
measurements. A local check is not general qualification.

[Single active plan](plans/video-to-agent-platform.md) · [Data audit](video-data-audit.md)
· [Metric definitions](driving-metrics.md) · [Architecture](architecture.md).

## Active session — run-033

Paths are relative to ignored `data/lab/coaching-reliability/`.

- `run-033/processed/crash-session/`:29,402 native1080p60 samples. Only pedals were
  re-extracted from the original video; other channels, qualities/reasons, missing
  values and CSV evidence were verified unchanged from run-031. No OCR.
- Source: `data/lab/2026-09-03-generic-s-fusion/crash-representative.mov`,453613415 bytes,
  SHA-256 `b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124`.
  Source identity, format/CFR, decoder timestamps and full coverage verified.
- Native pedal width144px fixes the old153px denominator. Validated profile mode
  `left_connected` measures contiguous fill from the left edge and includes empty
  rows in the spatial percentile. Colors and temporal thresholds are unchanged.
  Other profiles/default calls retain historical `longest_run` behavior.
- All58,804 parent pedal readings were reproduced alongside the new extraction.
  Manifest `pedal_refresh` records parent hashes/code, old/new modes and geometry.
  Inherited channels do not acquire the new extractor's provenance or qualification.
- `run-033/processed/control-episodes/`:83 episodes (37 brake,46 throttle),165 events,
  53 candidate intersections,81 resumption relations, no pedal gaps. Onsets, ends,
  confirmations, truncations, raw profiles and quality remain explicit.

Reproduction: [pedal refresh](session-artifacts.md), [episode export](control-episodes.md),
[signal semantics and calibration](signal-treatment.md). Use fresh output folders.

## What was checked, and what remains unknown

- Run-032's208 native frames in8 targeted windows were reused. Off/on12982/13018 is
  restored; delayed off2624 returns to2621. Sparse text/graphic pixels no longer
  sustain throttle. The visible pulse20190–20195 remains in raw readings but cannot
  satisfy100ms persistence; false episode20190–20305 disappears.
- Brake B2 boundaries11246/11423 remain unchanged. Existing human onset reference
  11245–11246 and provisional model end11422–11423 yield a local boundary-duration
  interval2.933–2.967s containing2.950s. Interior/physical latency remain unqualified.
- 21 existing annotated points per pedal: MAE brake0.188 and throttle0.143 point;
  all9 full-scale points remain100 %. Synthetic checks protect real1/2/3/7-pixel
  fills, intermediate levels, full bars with text holes, empty rows and isolated pixels.
- 379 full-suite tests passed plus one subsequently added configuration-validation
  test. Production code unchanged after the full-suite run. Source/parent/output
  hashes and preservation of all nonpedal evidence were verified.
- New visual references in run-032 are provisional non-blind model review, separate
  from human labels. Changed event counts do not validate every added/removed event.
  Last maximum, release onset, physical control latency and general timing accuracy
  remain unqualified. `s` is a fraction, not metres; `steering` is a HUD candidate,
  not a physical angle. Modern TC/ABS and run-024 lap-time readings remain unavailable.
- Existing historical gate results/targets remain unchanged; do not imply validated
  automated coaching from this capability-specific correction.

Delivery evidence: `run-033/reports/results.md`, `verification.json`,
`bounded-checks.json`, `calibration-points.json`, `tests-full.txt`.

## Reusable earlier evidence

- Run-024: original full extraction; run-031: width-calibrated pedal refresh. Both
  are preserved parents, not the current pedal baseline.
- Run-029: first episode implementation; run-030: width calibration evidence;
  run-032: frame-linked timing review and counterexamples, preserved unchanged.
- Run-021/run-022: frozen BMW/incidents counter truth; no exhaustive reread needed.
- Run-026: three reviewed Combes passages, native frames and `session_coaching.md`.
  Its [historical contract](specs/2026-09-13-session-coaching-report.md) is reproducible.
- Run-027: full-lap viewer,14 manually routed zones; [commands](perception-package.md).
  These are navigation windows, not automatic geometric landmarks. Check any local
  preview server before claiming it is running.
- Run-028: PDF and external response/evaluation remain a local experiment in visual
  reconstruction, not proof of general condensation or automated coaching.

Unused inherited defects: `generate_summary()` counts HUD numbers rather than complete
laps and returns0 for all-missing speed. Correct these before reusing those aggregates;
none is used by the new episode calculations.

## Exact next action

**Define the first spatial data increment using the three already reviewed Combes
passages and their native frames/landmarks.** Inventory measurable image placement and
missing geometry before promising trajectories in metres. Use run-033 for controls;
retain local timing limits and avoid another full pedal replay without a new defect.

ACC-on-Mac software/service and usable PC duration are unknown. Prepare any collection
before consuming a limited PC window. No paired dataset, spatial model training or
platform implementation has been launched.
