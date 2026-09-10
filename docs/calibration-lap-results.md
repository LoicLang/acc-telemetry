---
summary: exhaustive first BMW calibration-lap visibility evidence and current full-source replay, with development-only progress limitations
read_when:
  - assessing run-015 calibration or progress evidence
  - resuming native 1080p event validation after the first complete-lap visibility review
---

# First complete BMW calibration-lap review

Private evidence is under ignored `data/lab/coaching-reliability/run-015/`.
Source: BMW `/Users/loiclang/Movies/2026-09-03 22-42-08.mov`, SHA-256
`76859897055ddbac6bb52f6299dc7b86a6daf36bb3182b8d64d3da6c9aae378d`,
1,119,948,389 bytes. Native 1920×1080, exactly 60 fps constant presentation cadence
was verified before any new decoding.

## Selection and complete visual scope

The chronologically first complete candidate in the preserved run-011 BMW output
was selected before new coverage measurement. No speed or quality ranking was used.
The candidate report was used to locate boundaries, not as visual truth or as a
compatible acceptance fingerprint.

Root's separate direct image review confirms counter 0→1 between frames 17167 and
17168, and 1→2 between 25871 and 25872. Existing five-reading confirmation places
calibration boundaries at **17172 and 25876**, or **286.20–431.26666666666665 s**.
These are implementation confirmation times, not physical line-crossing truth.
The counter review covers only two selected windows, not all source events.

The frozen preparation covers frames **17160–25888 inclusive**: 8,729 images,
including 12 frames of padding on each side of the 8,705-frame calibration interval.
It contains 182 sequential speed sheets, 40 scene contexts and 42 boundary crops.
Existing overlapping run-011 crops were reused after hash and pixel checks.
`reports/dossier-integrity.json` verifies every sheet cell against its source-bound
crop, without substituting this structural check for visual review.

Two `gpt-5.6-sol` agents reviewed disjoint halves: frames 17160–21527 (4,368) and
21528–25888 (4,361). They inspected every cell of all 182 sheets at original detail,
plus scene contexts. **All 8,729 cells are visible/readable; absent 0, unknown 0.**
Per-frame decisions and reviewer identities are in `reports/lap-review-{a,b}.json`.
These are agent reviews, never user approval or numerical speed truth.

`processed/bmw-speed-visibility.json` combines the new review with preserved earlier
BMW reviews. It contains **8,910 reviewed visible frame cells** across the 47,589-frame
source; the other **38,679 are unknown**, not asserted absent. Agreeing contiguous
intervals merge while retaining contributing reviewer names. Sheet/agent boundaries
must not reset causal admission. Old review files and authorship remain unchanged.
The source-bound format and exact half-open boundaries pass validation.

## Replay method

A real pipeline smoke check on the first 40 source frames passes. The initial smoke
verification helper used the wrong dataclass attribute; the corrected helper accesses
`FrameObservation.observations`. Both logs and script versions remain preserved;
no repository code changed.

A single complete BMW replay runs the production `TelemetryPipeline` and writes new
telemetry-v2 artifacts. Its `reports/final-freeze.json` binds source, reviewed visibility,
settings, package modules, script, OCR asset and runtime, previous numerical/control
annotations and the new boundary review. No acceptance target, OCR setting, pedal
processing or 100 m/s² / 0.25 s speed-admission policy changed.

## Verified results

The full replay finishes in 687 seconds and exports all **47,589 frames**, with
exact frame/timestamp alignment against the preserved BMW capture evidence.
Artifacts are `processed/bmw-session/`; results are `reports/results.json`,
`bmw-progress.json` and `bmw-evaluation.json`.

| Scope | Images | Readable | Admitted speed | Speed abstentions | Available `s` |
| --- | ---: | ---: | ---: | ---: | ---: |
| Complete calibration interval, 17172–25876 | 8,705 | 8,705 | 8,679 (99.7013%) | 26 | 8,473 |
| Prepared interval including padding | 8,729 | 8,729 | 8,703 | 26 | 8,485 |
| Whole BMW source | 47,589 | 8,910 | 8,884 (18.6682%) | 38,705 | 8,924 |

On the full source, 38,679 speed abstentions are explicitly unreviewed HUD;
none of those frames is declared absent. The other 26 abstentions all occur inside
the calibration lap: 21 `speed_ocr_missing`, three `speed_out_of_range`, two
`speed_rate_exceeded`. Root visually reviewed all 26 output-selected crops in
`reports/abstention-visual-review.json`: the HUD remains readable, the 21 reads are
blank and the five numeric reads are wrong. This diagnostic review is not a new
independent sample or proof of accuracy on all admitted frames. No OCR adjustment
was made. Every rejected speed retains null, its raw text and its reason.

**One calibration lap is now accepted; previously none was accepted.** The effective
integrated length is **6,950.810185 m**. This is an internal estimated normalization
length, not a measured circuit length or metric spatial accuracy result. The other
two complete candidate laps remain rejected for missing speed coverage.

Calibration reports `missing_speed_fraction: 0`, although 26 measured speeds are
absent. This field counts missing **odometry edges after internal interpolation**:
`reports/odometry-diagnostic.json` reproduces 8,704 integrated edges, 8,659 observed
and **45 interpolated**, zero missing. The existing maximum gap remains 0.25 s.
Interpolation never replaces measured speed in observations or normalized samples.
The 1% calibration limit is unchanged. A relative MAD of zero from one accepted lap
is not a repeatability measurement; uncertainty 0.03 is a configured single-lap
fallback, not a calibrated confidence interval.

`s` is available on **8,473/8,705 calibration frames**: 8,399 fused, 72 predicted,
two observed boundary anchors; **232 remain missing** with `uncertainty_limit`
(227 also have `visual_ambiguous`). These provenance labels do not certify spatial
accuracy. On the two previously approved BMW landmark passages, only the first
has `s` (frame 25836, 0.995686, fused); the second remains unavailable. With only
one measured passage, dispersion and metric accuracy remain `not_evaluated`.

All **19/19 approved BMW numerical speed points remain exact**, MAE/P95 0/0 km/h;
all 564 fixed BMW segment frames are admitted. Their exact outputs match the scoped
run-014 replay. Across all 47,589 frames, raw speed OCR and both complete brake/throttle
observation records are unchanged versus the hash-verified run-011 artifact.
Only speed admission and its downstream estimated progress receive expanded evidence.
The two previously approved BMW lap events still match; the other predictions do
not become classified events without an exhaustive source review.

## Gate, preservation and next action

**Gate A still FAILS and B stays blocked.** This is one development calibration lap.
Exhaustive native 1080p event truth and a distinct pre-reserved independent recording
remain missing. Incidents V-CRASH-15 stays below 95% in the preserved scoped run-014
results; it was not replayed or tuned here. Whole-source speed visibility remains
mostly unknown. No numerical all-frame, pedal accuracy, latency, or spatial accuracy
claim was added. No holdout, 720p, R, B or separate replay research was processed.

No source, old review, approval, code or configuration was changed. The new reviews
retain both agent identities and their per-frame evidence. Final preservation checks,
focused/full tests, docs discovery and diff check are recorded in
`reports/final-verification.json`. The full suite remains **317 passing tests**.

Measurement fingerprint:
`15c70be35196dc8d377a3f12126fbd1ea647e8ff1ba3b77cde33ba6ae6655b8d`.
Results fingerprint:
`dc6860d3c6995ff5953a16bb13bba0910ca945b2e46d72dc9a13c71d4708d10c`.

Next action: prepare the exhaustive native 1080p lap-counter review dossier for the
BMW and incidents development sources, with source hashes and every frame accounted
for; reuse existing approved boundary windows without expanding their authority.
