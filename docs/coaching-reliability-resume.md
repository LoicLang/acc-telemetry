---
summary: concrete low-context execution guide for the remaining A6 human evidence and subsequent A7 gate
read_when:
  - resuming coaching reliability after the September 7 lineage handoff
  - preparing the final small annotation review
  - deciding whether A7 can start
---

# Resume A6, then A7

Read AGENTS.md, run `./scripts/docs-list`, read `current-status.md`, the active
specification and plan it names, then inspect Git. Do not load archived status by
default. The plan is authoritative; this guide identifies its exact remaining inputs.
All `run-*` paths below are under ignored `data/lab/coaching-reliability/`.

## 1. Verify existing evidence; do not repeat accepted work

Open `run-005/processed/accepted-corpus-v3/index.json` and its three source labels
and review reports. Confirm only `events` and `repeated_passages` fail readiness.
Verify referenced files exist. If local files are absent, report that limitation;
do not fabricate their contents from these summaries.

Development lineage is **finished**. The evidence is
`run-005/reports/development-lineage.json`. `resolve_lineage.py` computed file hashes
and compared every compressed video packet against the original using FFprobe
`-show_packets -show_data_hash sha256`. The clip is a contiguous original sequence
with +515 s PTS offset. `apply_lineage.py` copied v2 to v3 and asserted equality of
all annotation fields except `recording_id`, then revalidated reports/readiness.
Do not rerun these scripts over their existing outputs; use a new run if needed.
Do not ask the user for recording provenance again.

Approved readings and events originate in the three approval files listed by the
v3 index. Keep these snapshots immutable. A later corpus must retain v3 recording IDs
and holdout role; the existing `consolidate` command reads the old approval metadata,
so blindly reconsolidating those files would lose the independently resolved lineage.

## 2. Prepare only the missing human review

No new focused portal has been prepared in run-005. Build a small ignored review
package in a fresh run, using the existing native frames where possible:

1. **One additional pedal-event window:** E16 (506–510 s, holdout frames 30360–30600)
   is an existing candidate described by the user as exit acceleration. It has no
   accepted event timestamp. Images are in
   `run-004/processed/holdout-event-windows/frames/`; candidate ranges are in
   `candidates.json`. Present frame navigation and ask for the actual event type and
   frame/interval. Do not pre-approve an inferred timestamp. E01/E12 are also only
   descriptive; do not count them as timed events. If E16 has no measurable crossing,
   select a different short window instead of forcing it to count.
2. **Physical passages:** current labels contain zero reviewed physical landmarks.
   Current config requires two passages per source, so prepare six intervals total
   across BMW, incident clip, and holdout. Use a clearly identifiable **scene** feature
   repeated within each recording (e.g. the same transverse painted line). Define
   precisely which visible edge crosses which camera reference, and let the user
   confirm/correct the plausible frame interval. Do not infer this from `s_fused`,
   odometry, speed minima, timer reset or lap-counter changes.

Existing coarse sheets: `run-001/annotations-bmw/selection.html`,
`run-001/annotations-crash-clip/selection.html`,
`run-004/processed/holdout-lossless-selection/selection.html`.
Existing reported BMW lap markers L1 (431.2 s) and L3 (722.383333 s) can help locate
scene images; they are **not** reviewed physical crossings. Inspect before proposing.
Use native frames to review interval endpoints, not the coarse thumbnails.
Keep undecidable landmarks unknown. Never stamp `reviewed: true` on agent proposals.

Do not show H/M or the earlier accepted readings again. The user only needs to give
one event marker/type and review the six physical intervals, with corrections as
needed. Explain the limited scope in plain French. A6 explicitly requires human
review; elapsed time cannot satisfy it.

## 3. Consolidate actual review and close A6

Snapshot the user's response with source/frame/image identity and exact review scope.
Publish a new corpus rather than overwriting v3 or approval files. Preserve existing
labels, lineage and semantic context. Use `validate_annotations()` and
`corpus_readiness()` with the unchanged `config/validation.yaml`; do not lower minima.
Physical entries need kind `landmark`, unique ID, frame bounds, reviewed flag and a
stable definition identifying repeated passages. Keep event type and uncertainty.

All readiness checks must pass before checking off A6. If review is missing, update
handoff with the exact outstanding evidence and wait; **do not start A7 or B**.
Any reusable importer change needs focused RED tests, full suite and an atomic commit.

## 4. Execute A7 only after A6 acceptance

Follow every unchecked A7 step in `plans/2026-09-05-coaching-reliability.md`.
`scripts/validate_capture.py` and `tests/test_capture_validation.py` do not exist yet;
implement the plan, do not report an existing benchmark as independent validation.

- Test empty truth, identical bias, duplicate/missed/unmatched event cases first.
- Read telemetry-v2 artifacts without rerunning OCR in the validator. Measure field
  errors and coverage per source; publish denominators, exclusions and tolerances.
- Match events one-to-one; report annotation midpoint error, interval half-width,
  unmatched events and confirmation delay separately. Pedal latency concerns the
  first fresh 5% crossing, not the future B4 sustained coaching detector.
- Reviewed physical landmarks support repeated-passage dispersion of normalized `s`;
  they do not establish metric spatial error. Keep old replay counters diagnostic.
- Historical September 1 false-lap validation also needs independent annotation of
  **every real and suspect transition on the full capture**. Those annotations are
  not supplied by the recent A6 corpus. Prepare and obtain them if absent; do not
  substitute a clean clip or the detector's own output as truth.
- Recent clean/crash/BMW and reserved holdout evaluation must use the planned
  definitions. Existing approvals cover individual visibility readings; consolidated
  `visibility` spans are empty. Do not extend point approvals to entire clips.
  Obtain needed continuous-span review before claiming continuous control coverage.
- Preserve holdout reservation/fingerprint compatibility. Never fit extraction on it.
- Publish the six required `gate-a.json` checks and measurement fingerprint with
  evidence paths. Missing evidence is `not_evaluated`, not pass. All must pass for B.

Use the existing `.venv/bin/python`, FFmpeg and FFprobe. No new package/workflow is
required. Tests and small relevant media checks suffice while developing; do not
repeat expensive full replays without a changed component or unresolved failure.

## 5. Commit and hand off

Before each coherent commit: focused tests, full suite, `./scripts/docs-list`,
`git diff --check`. Keep the active plan checkboxes and current status synchronized.
Update `acc-ps5-plan.md` only if a stage gate or product direction changes. Commit
only code/tests/docs/config as appropriate; personal evidence stays ignored. Push
`codex/coaching-reliability` to origin; no merge to main is authorized by this task.
