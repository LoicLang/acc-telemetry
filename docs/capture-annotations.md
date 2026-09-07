---
summary: A6 independent annotation workflow, presentation-frame preflight, corpus requirements and pending human review
read_when:
  - preparing or reviewing capture annotations
  - validating visibility files for telemetry extraction
  - implementing A7 independent measurement benchmarks
---

# Independent capture annotations

A6 tooling is implemented. The prepared material contains **no inferred truth**;
review and corpus requirements remain pending. The CLI does not call OCR or use
`s_fused` to choose independent labels or physical landmarks.

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

## Corpus still required

`corpus_readiness()` checks the configured minima: 100 readable frames per speed,
brake and throttle, 20 degraded frames, 20 pedal-event windows, at least two recordings,
and repeated physical passages (initially two per recording). Reports must come from
validated labels, not inferred OCR. A7 will consume these inputs and measure errors.

Fill `recording_id` with the same original recording identifier for all derived clips
from that recording (the original source hash is suitable). The corpus accepts one
consolidated entry per recording, refuses duplicate source hashes or cross-role clips,
and stays pending without declared lineage. Adjacent frames cannot be split between
development and holdout. Previously used calibration/replay captures are development
material, not an untouched holdout. A new independent recording is still needed for
that final role, or the limitation must keep the holdout gate unvalidated.

## Verified local preparation (2026-09-06)

Ignored material under `data/lab/coaching-reliability/run-001/`:

- `annotations-bmw/`: 47,589 presentation frames; 80 selection images;
- `annotations-clean-clip/`: 18,902 presentation frames; 32 selection images;
- `annotations-crash-clip/`: 29,402 presentation frames; 50 selection images;
- `annotations-bmw/frames-d4bdcf363e28/`: three native preview frames, 6000–6002;
  initial labels hash was verified unchanged;
- `a6-corpus-readiness.json`: `not_evaluated`, zero reviewed readable/degraded/event
  counts. All three preparations are development material; none has reviewed labels.

The full incident source failed the preliminary coded-count check and was not rerun
with the corrected presentation-packet preflight; only its existing representative
clip is verified above. Old failure logs remain diagnostic history, not proof of
corruption. No video has been modified. Selected thumbnail/native examples were
visually inspected for output readability; no labels were approved by the agent.

## Review portal prepared after A6 interruption

An additional ignored review package is available at
`data/lab/coaching-reliability/run-002/reports/START_HERE.html`. It contains six
scoped windows and 501 native frames in total, with 16 assistant readings offered as
proposals only:

- B1: BMW braking window, 326.000–328.000 s;
- B2: incident clip braking window, 187.000–190.000 s;
- L1: BMW displayed lap transition, 431.000–431.500 s;
- L2: timer/lap counter offset at the start of the incident clip, 0.000–0.500 s;
- N1: BMW stationary neutral example, 0.000–0.250 s;
- R1: incident clip reverse example, 369.000–371.000 s.

The portal links each frame to its full native image plus HUD/counter crops and asks
for corrections by frame. `proposals.json` records the assistant visual read,
source hash, method and `reviewed: false`; it is not an annotation file and is not
used by A7. The generated contact sheets and `B2-reading.png` were visually checked
for readability. All sources remain development material previously used to tune the
extractor. This package intentionally does not claim a holdout or corpus acceptance.

The subsequent user response is retained in `run-002/reports/user-feedback.json`.
It confirms specific throttle-release markers, reported new-lap frames and N1
stationarity, not blanket approval of all 501 frames. Intermediate bars that were
previously unquantified now have manual pixel-length estimates and ruler images.
The apparent full-bar reference is distinguished from the wider extraction ROI;
neither that calibration nor the new percentages is independently validated yet.
No production detector output was used as the annotation reference.

The updated portal keeps throttle release separate from first visible braking.
For L2, the reported lap start/timer reset precedes the numeric-counter update by
four frames. Do not silently label the old counter digit as the new lap, or use
counter-update latency as physical crossing error without specifying that distinction.

The user subsequently approved the displayed batch. `run-002/reports/approval.json`
snapshots that approval with hashes of the reviewed proposals/feedback: 16 readings,
five intermediate estimates with tolerance and the event clarifications. The portal
marks this first review complete. The approval is scoped; it does not review every
field in every frame, establish recording lineage, or satisfy corpus/holdout gates.

## Second review batch (2026-09-07)

`data/lab/coaching-reliability/run-003/reports/START_HERE.html` offers eight new cards
with three proposed readings each (24 total): B3/B4/B5/B6 braking, G1/G2 release or
throttle modulation, L3 displayed lap transition, and D1 visibility near a barrier.
The user can respond by card/frame in chat; no JSON editing is required.

Full frame windows are recorded in `run-003/processed/review-index.json` and the two
selection JSON files. They contain 748 BMW and 724 incident-clip images (1,472 total).
The portal shows cropped native HUD/counter evidence plus a frame-by-frame viewer.
Fifteen intermediate pedal estimates retain hand-picked pixel endpoints and the
144-pixel reference scale accepted for annotation in batch 1. The stated tolerance
remains an annotation estimate, not a sensor accuracy claim.

`run-003/reports/proposals.json` keeps every new reading unreviewed. D1's driving
incident does not automatically count as an unreadable HUD or a degraded measurement.
The first batch approval remains unchanged; these 24 additional candidates neither
complete the 100-per-field requirement nor establish the event/degraded/holdout gates.
Native dimensions, image hashes and all static links were checked. The browser tool
could identify the tab but could not inspect this file URL under its URL policy;
interactive browser validation is not claimed.

The user subsequently approved the 24 displayed batch-2 readings and supplied an
exact L3 marker. `run-003/reports/approval.json` retains this scoped approval. Together
with batch 1 there are 40 accepted image readings; unexamined native frames and
corpus/holdout acceptance remain pending.

The user also explained B6's downshift throttle spikes as automatic blips. Keep the
HUD measurements intact, but distinguish displayed throttle from intentional driver
pedal action when designing coaching events. This user-reported context must not be
generalized to every overlap without evidence, or used to label it a driving mistake.
