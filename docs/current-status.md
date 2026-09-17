---
summary: public community handoff of the paused video project; future PC work starts on a separate foundation
read_when:
  - resuming or maintaining this published video research snapshot
  - distinguishing included code from private local experiments and future PC work
---

# Community handoff

**Status: community handoff · 17 September 2026.** The owner is moving to PC and has
stopped the video-first/model roadmap. This repository preserves the existing work
for others to study or continue. The future PC-based project will start separately,
after identifying the telemetry actually available on that platform.

Reference roadmap: `plans/video-to-agent-platform.md` (**frozen**, not an active queue).

Do not automatically restart dense mask annotation, model training, video processing,
or platform/MCP development from earlier task instructions. No PC collector or new
project has been created as part of this handoff.

## What a fresh clone can use

- Video extraction, normalized domain data, versioned artifact read/write/validation.
- Native1080p60 format/clock checks, fresh speed/gear/lap-counter observations.
- Pedal calibration144px and `left_connected` fill extraction for the native profile.
- Candidate control episodes with frame evidence, timing, nulls, gaps and truncations.
- Synthetic demo, small public test fixtures, full unit tests and CI configuration.
- Technical documentation, historical result summaries and known limits.

Start with the [README](../README.md), [synthetic demo](../scripts/demo_control_episodes.py),
[contribution guide](../CONTRIBUTING.md), [architecture](architecture.md),
[capability audit](video-data-audit.md) and [episode contract](control-episodes.md).

## What is not distributed

Personal captures, full session exports, OCR assets, annotated frame collections,
generated reports, spatial experiment scripts/labels and trained checkpoints remain
local and ignored. Paths under `data/lab/.../run-*` throughout the technical/history
docs identify experiments; they are **not a bundled public dataset**.

The code can run on your own compatible capture. Exact reproduction of the private
experiments requires their original inputs and is not possible from this clone alone.
The synthetic demo and unit tests do not require those inputs.

## Frozen outcomes and evidence limits

- **Run-033** was the final local control baseline:29,402 native frames, only pedals
  re-extracted; inherited channels/quality/reasons/missing values preserved.83 candidate
  episodes (37 brake,46 throttle),165 events,53 candidate intersections.
- The native pedal fix rejects disconnected HUD text fragments without smoothing
  samples or raising event thresholds. Local validation:21 points per pedal, MAE
  brake0.188/throttle0.143 percentage points;9 full-scale points at100 %. These are
  recorded local results, not a general error guarantee for arbitrary captures.
- **Run-034** fitted a tiny appearance classifier on two images and checked four other
  images from the same source.28/35 provisional patches correct; confusion with runoff
  and barriers remained. No reliable dense segmentation or metric trajectory resulted.
- `s` is normalized progress, not metres; `steering` is a HUD candidate, not a physical
  angle. Physical input latency, vehicle pose, lateral trajectory and modern TC/ABS
  intervention semantics remain unavailable/unqualified.
- Historical validation targets/results are preserved; they must not be promoted to
  claims of validated automated coaching. The inherited `coaching_eligible=false`
  metadata remains historical behavior, not a milestone for the future PC project.

[Signal/calibration details](signal-treatment.md) · [Spatial feasibility](spatial-feasibility.md)
· [Archived measurement history](archive/README.md).

## Known continuation work

For someone choosing to continue the video approach: acquire an independent capture,
review HUD visibility/calibration, and validate the capability of interest before
relying on full-session metrics. Spatial development needs dense semantic labels,
occlusion handling and a justified metric reference; that work was deliberately paused.
Unused inherited summary defects are documented in the audit (HUD number counts versus
complete laps, zero returned for an all-missing speed aggregate).

## Publication and origin

All implemented pedal/episode changes are included. The public entry point is `main`,
with a dated `video-handoff-2026-09-17.1` snapshot tag. Source history and upstream
attribution are retained. No project license has been invented for inherited code;
see [NOTICE.md](../NOTICE.md).

For the owner, the next step is a **separate PC acquisition inventory** after the PC is
available: actual exported fields, units, update rates and synchronization. No assumption
that every catalogue metric is available directly, and no automatic reuse of the video
extractor as the foundation of that new project.
