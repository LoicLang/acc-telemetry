---
summary: A6 independent annotation workflow, accepted corpus and remaining A7 measurement limitations
read_when:
  - preparing or reviewing capture annotations
  - validating visibility files for telemetry extraction
  - implementing A7 independent measurement benchmarks
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

## Consolidated scoped approvals

`scripts/annotate_capture.py consolidate --approval APPROVAL_1.json APPROVAL_2.json
--output NEW_DIRECTORY` verifies approved image hashes and source metadata, deduplicates
identical readings, refuses conflicts and publishes per-source labels/reports atomically.
Original approval snapshots are unchanged. The current result is ignored under
`run-004/processed/accepted-corpus/`.

Consolidated rows use explicit `review_scope: provided_fields_only`: unreviewed metadata
such as steering visibility or degradation may stay null. Defined numeric/text values
still require reviewed visibility; null does not count as degraded or invisible.
The original default fully-reviewed-row validation remains strict.

Lift and brake markers in one reviewed clip share `event_window_id` and count as one
window. Reported lap starts with `physical_landmark_reviewed: false` remain available
as temporal evidence but do not satisfy the physical-passage requirement. The current
corpus has 40 unique readable frames per target field and two reviewed pedal windows;
remaining minima, recording lineage and holdout are explicitly pending.

Source role/lineage declared in a scoped approval are now preserved by consolidation.
An explicitly approved degradation boolean is retained; unknown degradation remains
null. This supports real absent-HUD annotations without silently turning them into
development data or readable zeros. Synthetic regressions cover those boundaries.

## September 4 holdout and remaining review (2026-09-07)

The user supplied `/Users/loiclang/Movies/2026-09-04 22-30-22.mov` as a new source,
including a settings-menu interval after a crash. Its identity and measurement code
were reserved before inspection in `run-004/reports/holdout-reservation.json`.

Its only irregular PTS interval is at the very end. A byte-copy cut also left an
irregular dependency tail, so neither original nor byte-copy prefix was admitted as
a fully supported CFR capture. The retained first 895 seconds were losslessly encoded
to `run-004/interim/holdout-lossless-prefix.mp4` (approximately 19 GiB). Complete
framemd5 comparisons verify all 53,700 decoded images, timestamps and durations equal
the original prefix; preflight of the derivative passes. No interpolation or capture
repair is claimed, and the original file is unchanged. The exclusion and lineage are
explicit in `run-004/reports/holdout-lossless-transform.json`.

The holdout is scoped to this regular prefix. Measurement modules and settings remain
unchanged from the pre-inspection reservation; this source was not used to fit the
extractor. Its annotations are still proposals, not accepted truth or accuracy results.

`run-004/reports/START_HERE.html` presents:

- H01–H60: 60 manually read speed/gear/lap/pedal proposals, with visual pedal estimates
  rounded to five points and a proposed ±5-point annotation tolerance;
- M01–M20: native menu images at 541–560 s, proposing absent racing HUD values as null,
  with false visibility and explicit degradation. Menu control widgets are not racing HUD;
- E01–E20: 20 visually selected candidate windows, 4,820 native frames total, with
  unknown event presence/timestamp until the user identifies a frame/type or says none.

The existing two accepted batches remain untouched. If H/M are accepted, they can
complete the readable/degraded frame minima with the existing 40 readings. Event,
physical-landmark and lineage requirements still need their own evidence; merely
preparing 20 candidate windows does not satisfy the event gate. Static link/image/hash
checks are recorded in `run-004/reports/final-review-checks.json`.

The user's subsequent review accepted uncorrected H/M values under their standing
review convention and supplied 21 precise markers across 17 E windows. Approval is
stored in `run-004/reports/approval.json`; the consolidated corpus is now
`run-004/processed/accepted-corpus-v2/`. It contains 100 readable labels per target
field, 20 real degraded/menu cases, and 19 timed event windows including the earlier
two. E01/E12/E16 remain descriptive, without fabricated timestamps. The user's E17
steering explanation remains a hypothesis. Lineage for development recordings and
reviewed physical landmarks remain outstanding alongside the twentieth timed window.


## Lineage checkpoint before final review (2026-09-07)

The lineage checkpoint was `run-005/processed/accepted-corpus-v3/`. It is a
copy of v2 with only the two development recording IDs resolved from local file
and packet hashes. `run-005/reports/development-lineage.json` proves all 29,416
incident-clip video packets match a contiguous sequence of the September 2 22:40:01
original with constant +515 s PTS offset; the BMW original hash also matches.
No accepted human label, event or role changed, and v2/approvals are untouched.
At that checkpoint only events (19/20) and physical passages (0 reviewed per source;
two required) remained incomplete. The final scoped review below closes those inputs.
Follow `coaching-reliability-resume.md` for the accepted corpus and subsequent A7 work.

## A6 corpus accepted (2026-09-08)

The authoritative corpus is `run-007/processed/accepted-corpus-v4/`. The user accepted
all six run-006 physical intervals and identified E16 reaching full throttle at frame
30397 (506.616667 s), with roughly 60% throttle already present at the window start.
The rough percentage remains context only. This is a full-throttle marker, not a
5% onset; A7 must exclude it from that latency denominator and report event subtypes.
A discrete frame marker does not imply zero timing uncertainty.

The exact scoped response and endpoint/image identities are in
`run-007/reports/approval.json`. Existing labels, roles, lineage, visibility spans and
approval snapshots are unchanged. All configured corpus checks pass (100 per readable
field, 20 degraded, 20 timed windows, two physical passages per each of three sources).
Proof: `run-007/reports/a6-acceptance.json`. Gate A still requires A7 measurement
validation, historical transition truth and applicable continuous visibility evidence.
