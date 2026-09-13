---
summary: source-bound annotation tooling and targeted review contract, with general corpus work explicitly deferred
read_when:
  - preparing or reviewing capture annotations
  - validating visibility files for telemetry extraction
  - preparing general independent measurement benchmarks after the first export
---

# Independent capture annotations

A6 tooling and corpus acceptance are complete. Prepared proposals are distinct
from the scoped human approvals in the accepted v4 corpus. The CLI does not call
OCR or use `s_fused` to choose independent labels or physical landmarks.

## Two-pass preparation

```bash
PYTHONPATH=src .venv/bin/python scripts/annotate_capture.py prepare \
  --video INPUT.mov --profile ps5_full_map_1080p \
  --output data/lab/example/processed/annotations --role development
```

First pass writes source identity, `ffprobe.json`, `capture.json`, `selection.html`,
480x270 selection thumbnails every 10 seconds, blank `labels.json`, `selection.json`
and `REVIEW.txt`. Open the HTML sheet and choose windows in `selection.json`:

```json
{"windows": [{"frame_lo": 6000, "frame_hi": 6060}]}
```

These are illustrative frame numbers, not an annotated event. Intervals include both
ends, must be sorted, non-overlapping, and within the video's presentation frames.

```bash
PYTHONPATH=src .venv/bin/python scripts/annotate_capture.py prepare \
  --video INPUT.mov --profile ps5_full_map_1080p \
  --output data/lab/example/processed/annotations \
  --selection data/lab/example/processed/annotations/selection.json
```

Second pass creates a new `frames-<id>/` child with **every selected native frame** and
its own blank labels/manifest. Existing annotations and source videos are not changed.
Use native frames for measurement labels; thumbnails are only a selection aid. Choose
all required windows for a source in one selection, then review the resulting file.
Do not combine the coarse sheet and its selected frames as duplicate independent data.

## Preflight and decode evidence

Explicit profile resolutions and validation targets live in `config/validation.yaml`.
A separate validated loader avoids adding coaching configuration prematurely.

FFprobe supplies `best_effort_timestamp_time`, stream time base and frame rate. A6
requires increasing timestamps, CFR within stream timestamp precision, and alignment
of video-relative PTS with frame/fps within one frame interval. Unsupported resolution,
VFR/incompatible timing, unavailable frames and decoder errors refuse preparation.

For MOV, `nb_frames` can count coded packets that are not presentation frames. Local
checks found 1 discard packet in the recent BMW source, 92 in the clean derived clip,
and 14 in the crash derived clip. FFmpeg marks these packets `D`; its installed
`libavcodec/packet.h` defines them as necessary to decoder state but not output.
A6 compares decoded frames one-to-one against sorted **non-discard packet PTS** instead
of treating the coded counter as the presentation count. A regression verifies that
removing a genuinely expected presentation frame still fails. This packet/frame
contract is conservative: unsupported packetization is refused, not approximated.

`VideoProcessor` records decode status and refuses early EOF; when a coded-count
mismatch occurs on a real file, it checks the non-discard presentation packet count.
The shared pipeline retains that status in video metadata. Annotation preflight also
checks PTS/profile; a decode counter alone does not validate measurement accuracy.

Failed preflight can leave a separately named `*-failed-<id>.json` diagnostic with raw
FFprobe evidence, never a successful annotation directory. `--probe-evidence PATH`
can reuse that frame probe after matching source SHA-256/profile and freshly checking
presentation packets. This avoids repeating expensive decoding after an interrupted
or diagnosed preparation. Successful publication uses exclusive atomic directory
rename; raw/existing/source destinations are refused.

## Review contract

`labels.json` has schema `capture-annotations-v1`, source SHA-256, one source role
(`development` or `holdout`), `recording_id`, annotator and a top-level reviewed flag.
Frames contain frame/time, literal speed/gear/lap text or null, throttle/brake estimates
and tolerance in percentage points, per-field visibility, degradation and review flags.
Passages contain a unique id, kind (`landmark`, `lap_boundary`, `pedal_event`), inclusive
frame interval and review flag; pedal events also require throttle/brake field.

- Transcribe the HUD targeted by the profile, not a different cockpit display that
  may show another value or update at a different instant.
- Use null for unreadable text or unmeasurable pedals; do not infer zero.
- Review each visibility/degradation flag explicitly. Continuous visibility spans
  must not contradict reviewed occluded frames and omit overlays/menus.
- Physical landmarks must be defined from cockpit imagery, independently of minimap
  progress. Annotate a plausible crossing interval instead of inventing an exact time.
- Only set row and top-level `reviewed: true` after human review and name the annotator.

```bash
PYTHONPATH=src .venv/bin/python scripts/annotate_capture.py validate \
  --annotations data/lab/example/processed/annotations/frames-ID/labels.json
```

Validation rejects unreviewed, out-of-range, nonfinite, reversed, conflicting or
source-mismatched labels. Valid reviewed spans export to a **new** `visibility.json`
compatible with A3. Existing exports are refused. A reviewed empty truth set returns
`not_evaluated` with `error: null`, never zero error. Per-file `pass` means structural
review validity only, not accuracy or corpus acceptance.

## General qualification corpus (deferred from the first export)

`corpus_readiness()` checks the configured minima: 100 readable frames per speed,
brake and throttle, 20 degraded frames, 20 pedal-event windows, at least two recordings,
and repeated physical passages (initially two per recording). Reports must come from
validated labels, not inferred OCR. The A7 validator consumes these inputs and measures errors. These corpus minima are
not prerequisites for the experimental first text export; that report requires local
evidence for the facts it actually uses.

Fill `recording_id` with the same original recording identifier for all derived clips
from that recording (the original source hash is suitable). The corpus accepts one
consolidated entry per recording, refuses duplicate source hashes or cross-role clips,
and stays pending without declared lineage. Adjacent frames cannot be split between
development and holdout. Previously used calibration/replay captures are development
material, not an untouched holdout. A new independent recording is still needed for
that final role, or the limitation must keep the holdout gate unvalidated.

## Preserved approvals and current use

Historical preparation, approvals, source lineage and accepted A6 corpus are preserved
in [the annotation history](archive/reliability/capture-annotations-history.md).
The accepted corpus is run-007/processed/accepted-corpus-v4; do not rewrite its labels,
roles or event semantics. In particular a full-throttle marker is not a5% onset,
and an initial release is not a falling5% threshold crossing.

For the first `session_coaching.md`, use only targeted review of the chosen landmarks,
values and intervals. Selection may be manual and source-bound. Do not restart corpus
completion or exhaustive review. Follow [the active report contract](specs/2026-09-13-session-coaching-report.md)
and [current status](current-status.md).
