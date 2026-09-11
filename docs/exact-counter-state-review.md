---
summary: complete BMW fixed-ROI counter review, exact pixel mapping and scoped run-021 event and observation results
read_when:
  - resuming the counter review after sustained Astra inconsistency
  - interpreting exact-pixel equivalence and its limited annotation scope
---

# Exact counter-state review — BMW complete

The owner resumed after the run-020 shutdown checkpoint. The primary agent finished
all44 state sheets; new compiled labels and measurements are frozen in ignored
`data/lab/coaching-reliability/run-021/`. The original pause checkpoint and its ledger
prefix remain intact; run-020 review rows were appended after actual visual inspection.

## Why the method changed

The sustained Astra attempt again gave inconsistent readings: some frames104–116
point to the identical native PNG but were alternately read0 or unknown. The saved
`reports/protocol-audit.json` confirms one image per call, not multi-image batching.
The cause remains undiagnosed. The original Astra ledger is diagnostic, not accepted
truth; this does not establish a video change or application OCR defect.

The first40-sheet BMW scope contains3840 frames but only366 distinct raw RGB matrices
inside the existing numeric-counter ROI. Reclassifying an identical matrix repeatedly
adds no new pixel information and had produced contradictory labels. The new method
reviews each distinct matrix once and retains an explicit exact mapping for every
source frame. It is not the earlier claim that every original sheet was visually read.

## Exactness and scope

The ROI is the existing profile's `lap_number_training` rectangle `(270,105,58,60)`.
Original source crops remain intact. No threshold, quantization, approximate similarity,
OCR, interpolation or carry-forward is used. Each source frame still has its own time
and group membership. Unreviewed matrices stay unreviewed.

An independent gpt-5.6-luna mechanical audit verifies **all47589 BMW source rows**,
35546 original crop paths, **4159 exact RGB groups**, and all44 generated state sheets.
Every member's decoded matrix is byte-for-byte equal to its representative; every
frame belongs exactly once. Sheet tiles match2× nearest-neighbour display copies of
those matrices. Proof: `reports/exact-mapping-audit.json` and `audit_exact_mapping.py`.

This proves equality only inside the fixed ROI. It does not establish semantic labels,
full-frame/HUD context, physical line crossings, spatial accuracy or independent
acceptance. Any eventual mapped label must retain its representative review and equality
provenance; never present mapping as separate manual inspection of every duplicate frame.

## Completed BMW result — run-021

The primary agent visually inspected **4,159 distinct RGB matrices on44 sheets**, all
readable. This is a review of unique fixed-ROI states, mapped to **47,589 source frames**
by exact byte equality; it is not a claim of manual review of all496 original sheets.
The label ledger preserves each sheet hash, inclusive ranges and reviewer identity.
No rejected Sol/Astra labels were imported. No user approval is implied.

The compiler rechecks every source crop's hash and decoded ROI against its representative,
all sheet hashes, the original pause-ledger prefix, source SHA/size, artifact payloads,
current extraction modules and resolved settings. All pass. It retains each frame's
source PTS, group, representative, literal label and reviewer. No gaps or unknown labels
remain inside this numeric ROI. The initial3840-frame lot covers366 states and agrees
with all21 predeclared native QA references.

| Numeric change | Last old → first new frame | First new digit (s) |
| --- | --- | --- |
| 0→1 | 17167→17168 | 286.133333 |
| 1→2 | 25871→25872 | 431.200000 |
| 2→3 | 34630→34631 | 577.183333 |
| 3→4 | 43342→43343 | 722.383333 |

These are all four changes in the mapped ordered sequence; no reset or other numeric
change appears. No boundary is invented before/after the source; its initial and final
lap fragments remain partial. Literal frame counts:0=17168,1=8704,2=8759,3=8712,4=4246.

The unchanged run-015 full BMW extraction has **47,589/47,589 exact fresh lap-number
observations**, zero missing/wrong/nonfresh observations, against these labels. This
measures extraction observations, not the normalized confirmed lap state, speed,
physical lap timing or full telemetry accuracy.

All4 events match with no miss, duplicate or unmatched prediction: scoped precision
and recall1.0. P95 midpoint error is **0.008333s**, equal to the half-width of each
one-frame annotation bracket. First candidate is exactly the first frame displaying
the new digit; confirmation follows **0.066667s** later. The unchanged1s association
window and0.10s P95 target yield `fixed_roi_event_status: pass` for BMW only.

Evidence under run-021: `reports/bmw-numeric-truth.json`, `bmw-results.json`,
`result-audit.json`, `integrity.json` and `processed/bmw-fixed-roi-labels.jsonl`.
The scripts `evaluate_bmw.py` and `verify_results.py` retain the reproducible checks;
outputs are created exclusively and old reports are never overwritten.

## Remaining scope

Incidents review is now complete in run-022:24,267 manually reviewed unique RGB states,
29,402 exact mapped source frames,29,402/29,402 observed counter reads exact and4/4 events,
zero misses/extras, P95 8.3ms. The incidents measurement uses the isolated counter path,
not a full telemetry-v2 artifact. See [incidents-counter-results.md](incidents-counter-results.md)
for evidence, null freshness metadata and the unchanged L2 channel distinction.

**Gate A remains FAIL; B/R remain blocked.** Both fixed-ROI reviews are development
measurements, not full-scene context, physical crossings or independent acceptance.
Speed coverage, numerical speed truth and independent recording evidence remain separate
blockers. No application code, configuration, threshold, source or old approval changed.

Next: replay the incidents full shared telemetry pipeline with existing visibility evidence,
compare its counter output against run-022 truth, and preserve missing speed explicitly.
