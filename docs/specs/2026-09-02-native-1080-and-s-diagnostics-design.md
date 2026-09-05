---
summary: design for a native ACC PS5 1080p profile, controlled OCR comparison, and evidence-first s diagnostics
read_when:
  - implementing the PS5 1080p telemetry profile
  - benchmarking OCR by capture resolution
  - diagnosing the initial s anchor and saturation failure
---

# Native 1080p and `s` diagnostics design

## Goal

Adopt native 1920x1080 at 60 FPS as a candidate capture baseline, measure whether it
improves OCR, and produce enough internal position evidence to identify the cause of
the invalid `s` progression before choosing a fix.

This milestone does not attempt to complete robust lap transitions or end-to-end
quality propagation. It must not implement corner segmentation or coaching logic.

## New evidence

Two immutable external captures are available:

### Primary clean session

- Source: `/Users/loiclang/Movies/2026-09-02 21-55-05.mov`
- Format: H.264 High, 1920x1080, constant 60 FPS, YUV 4:2:0, BT.709
- Duration: 2326.033333 seconds
- Video bitrate: approximately 9.0 Mb/s
- Driving context: BMW M4 GT3, clean and consistent session
- Visible evidence: lap 1 around 300 seconds, lap 5 around 900 seconds, lap 9 around
  1500 seconds, and lap 12 around 2100 seconds
- Role: profile calibration, OCR measurement, and primary `s` diagnosis

### Secondary robustness session

- Source: `/Users/loiclang/Movies/2026-09-02 22-40-01.mov`
- Format: H.264 High, 1920x1080, constant 60 FPS, YUV 4:2:0, BT.709
- Duration: 1137.016667 seconds
- Video bitrate: approximately 7.1 Mb/s
- Driving context: recent car change with crashes and less consistent driving
- Role: later robustness checks for imperfect passages, OCR instability, and false
  transitions; not the truth source for driving consistency

The source files remain read-only. Initial diagnostics may generate ignored clips,
frames, CSV files, or reports under `data/lab/`. This milestone does not move, delete,
or commit either source video.

## Approaches considered

### A. Explicit 1080p profile — selected

Add `ps5_full_map_1080p` beside the existing 720p profile. Seed its regions from a
1.5x geometric scale, calibrate them on real frames, and retain explicit values in
versioned configuration.

Advantages: small change, current profile-selection path already supports it,
resolution-specific behavior is visible, and regressions are easy to test.

### B. Automatic ROI scaling — rejected for this milestone

Derive every region dynamically from a reference resolution. This is attractive only
after two explicit profiles prove that HUD geometry truly scales uniformly. Doing it
now would combine calibration with a configuration refactor and make failures harder
to attribute.

### C. Downscale all 1080p captures to 720p — retained only as the control

This preserves compatibility but throws away the detail being evaluated. A downscaled
version of the same primary frames is useful as the A/B control, not as the new target
pipeline.

## 1080p profile design

The new profile uses explicit integer regions. Initial coordinates use 1.5x scaling
from `ps5_full_map_720p`, rounded to cover the full scaled source region:

| Region | x | y | width | height |
|---|---:|---:|---:|---:|
| throttle | 1758 | 1005 | 153 | 21 |
| brake | 1758 | 1025 | 153 | 18 |
| steering | 1703 | 993 | 201 | 14 |
| lap_number | 356 | 107 | 71 | 56 |
| lap_number_training | 272 | 107 | 71 | 56 |
| last_lap_time | 179 | 131 | 131 | 30 |
| speed | 1766 | 932 | 81 | 48 |
| gear | 1686 | 887 | 71 | 108 |
| track_map | 5 | 323 | 404 | 275 |

The existing PS5 white bounds and 60-frame full-video sampling remain the initial
position-extraction defaults. Real-frame inspection may adjust region edges, but any
adjustment must be justified by a saved local diagnostic and covered by a profile
test.

The existing CLI and web selectors already accept explicit configured profile names.
No new resolution-routing abstraction is required.

## Controlled OCR comparison

Resolution must be evaluated on the same visual evidence:

1. select representative frames from the primary native 1080p source;
2. create a 1280x720 downscaled version of those same frames using the existing video
   processing assumptions;
3. use the 1080p profile on native frames and the 720p profile on downscaled frames;
4. manually record visible lap number and last-lap time as ground truth;
5. compare exact lap-number matches, non-empty valid lap-time matches, speed, and gear;
6. preserve the local results in an ignored lab report and summarize the conclusion
   in `docs/current-status.md`.

The minimum sample covers multiple lighting/background conditions and at least six
confirmed lap transitions from the clean session. Full-video extraction begins only
after sampled regions and OCR results are plausible.

Success means the 1080p profile reliably extracts controls, speed, gear, lap number,
last-lap time, and the full map from the sampled evidence. Adoption as the new default
requires a measurable OCR benefit or a clear quality/resilience benefit; file
resolution alone is not evidence.

## Position diagnostic boundary

The legacy telemetry output is not expanded speculatively. Instead, position tracking
exposes a focused diagnostic record for the most recent observation. The diagnostic
must distinguish:

- detected red-dot coordinates or missing detection;
- closest path index;
- current start index and start source;
- inferred travel direction;
- raw path position before completion handling and validation;
- completion handling, if applied;
- validated output position;
- validation decision such as observed, missing-held, backward-held, jump-clamped,
  smoothed, forced-completion, or lap-reset.

Normal callers may ignore this record. A local diagnostic runner collects it with
frame number, timestamp, raw lap observation, and confirmed lap state. Default CSV and
API compatibility do not change in this diagnostic slice.

## `s` investigation protocol

Use the primary clean session first:

1. reproduce the current output with the 1080p profile;
2. identify the first early plateau and first premature completion;
3. trace backward from validated output to completion handling, raw projection,
   direction inference, anchor source, closest path index, and red-dot observation;
4. compare the same physical passage across several clean laps;
5. state one root-cause hypothesis and test it with the smallest synthetic regression;
6. do not implement a production correction until the evidence identifies the first
   bad transition in the data flow.

After the clean trace is understood, run the secondary session only as a stress case.
Crashes and resets must not be used to define normal progress behavior.

## Test strategy

Versioned tests cover:

- exact existence and geometry of `ps5_full_map_1080p`;
- component construction with the new profile;
- full-map bounds and sampling settings;
- each position-diagnostic decision using synthetic paths and mocked dot positions;
- unchanged legacy `track_position` output when diagnostics are ignored;
- the smallest synthetic trace that reproduces the confirmed initial-anchor failure.

Real video, extracted frames, full telemetry, and generated reports remain ignored
local integration evidence. The repository records their summarized measurements and
reproduction command, not personal media.

## Commit boundaries

1. design and activate this milestone in repository status;
2. add the tested explicit 1080p profile;
3. record the sampled 1080p-versus-720p OCR result and baseline decision;
4. add tested position diagnostics without changing legacy output;
5. reproduce and document the first bad `s` transition;
6. stop for review before implementing the production `s` correction.

Every behavior commit includes focused tests, the full suite, and the corresponding
status update when the verified project truth changes.

## Exit state

At the end of this milestone:

- native 1080p support is either validated or rejected with measurements;
- the clean session has a reproducible `s` trace;
- the first invalid state transition is identified or the remaining uncertainty is
  narrowed to one explicitly testable hypothesis;
- no corner, coaching, robust-lap-transition, or end-to-end quality feature has been
  started;
- the next production correction requires a separate review decision.
