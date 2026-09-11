---
summary: paused run-020 exact RGB counter-state mapping, independent mechanical audit and partial primary-agent semantic review
read_when:
  - resuming the counter review after sustained Astra inconsistency
  - interpreting exact-pixel equivalence and its limited annotation scope
---

# Exact counter-state review — paused

The owner requested shutdown. No job remains active. Resume at ignored
`data/lab/coaching-reliability/run-020/START_HERE.md` and
`reports/pause-checkpoint.json`.

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

## Exact pause point

Primary agent visually inspected **sheets1–12, groups0–1151 inclusive**, representing
1152 distinct matrices. All these matrices show literal0, visible. The per-sheet source
hashes, group ranges and reviewer are recorded in `reports/root-exact-state-review.jsonl`.
Sheet12 was appended before pausing. The first366 matrices needed by the initial3840-frame
batch are within this review, but no final per-frame result or gate verdict was published.

**Groups1152–4158 remain semantically unreviewed.** The next image is
`processed/bmw-exact-states/013.png`, groups1152–1247. Display it at original detail,
inspect every matrix, then append actual ranges with `append_state_review.py`.
Continue through sheet44 before compiling and validating full-source fixed-ROI labels.
Do not infer later values from the previously reviewed zeros.

Incidents mechanical inventory:29402 frames and24267 distinct RGB matrices. No semantic
exact-state review was started for that source. Previous eight targeted event checks
remain scoped; no exhaustive recall claim or new gate pass follows from this pause.

**Gate A remains FAIL; B/R remain blocked.** No code/configuration/threshold, old review
or source file changed. Pause tests and docs checks are saved in `run-020/reports/`.
