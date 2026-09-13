---
summary: reviewed and automatic speed visibility semantics and preserved provenance
read_when:
  - extracting modern speed with CLI or web service
  - preparing reviewed speed visibility or evaluating its source binding
---

# Reviewed speed visibility

The default `reviewed` measurement mode requires reviewed visible HUD. Without a review, or in absent/unknown
intervals, speed is missing with `speed_hud_absent` or `speed_hud_unverified`.
The extractor retains its one raw OCR read and reasons even when admission fails.
Inside a visible interval, black/empty ROI still abstains. A readable zero remains
zero; it is never inferred from missing HUD. Explicit legacy extraction is unchanged.

For the owner-requested automatic trial, `--measurement-mode automatic` reads the
whole source without annotation inputs. Unknown visibility no longer prevents a
numerically admissible fresh reading, but `speed_hud_unverified` remains attached.
Empty/black ROI, invalid text and numerical admission failures still abstain. This
is an explicit development mode, not a qualified automatic HUD detector. The pipeline
rejects annotation inputs in this mode; use them only for separate validation.
The manifest records the mode; `coaching_eligible` stays false. See
`automatic-system-trial.md` and the12 September clarification in `signal-treatment.md`.

The CLI accepts `--speed-visibility-json PATH` separately from pedal/steering
`--visibility-json`. The web processing Python service accepts
`speed_visibility_json`; HTTP forms do not expose reviews yet and therefore default
to missing speed. Old pedal review files do not approve speed by implication.

A review is a JSON object with exactly `schema_version: "speed-visibility-v1"`,
`source_sha256` (64 lowercase hex characters), `source_size_bytes` (positive integer)
and `spans`. Each span has `start_s`, `end_s`, `state` and `reviewer`.
States are `visible`, `absent`, `unknown`; visible means speed HUD readable, not merely
some numeric text. Every span needs a nonempty reviewer, including uncertainty reviews.
Times are video-relative seconds, start included/end excluded. Intervals must be
finite, sorted, non-overlapping, nonnegative and within video duration. Uncovered
time is unknown. Source hash/size are checked against the actual video before reads.

The pipeline exports the consumed review in resolved configuration and telemetry-v2
manifest, preserving its source identity, intervals and reviewer names. Export and
reload reject a review/source mismatch. Old artifacts without this field remain
readable and retain their original quality, including HELD. Their absence of review
must never be retroactively interpreted as a new approval.

This is reviewed admission, not an automatic HUD detector or a numerical accuracy
guarantee. A visible HUD can still be misread. A9 numerical admission also checks
the configured rate envelope within the same reviewed interval, with gaps and new
intervals resetting temporal support; see `archive/reliability/admission-correction-results.md`.
New development visibility must be
reviewed from pixels with its author recorded; model outputs cannot supply truth.
Missing whole-source review can reduce speed/odometry/calibration availability and
must remain explicit. Gate A still requires independent compatible measurements.

Software evidence: run-011 `reports/hud-red.txt` (two real functional failures),
`hud-artifact-binding-red.txt` and corresponding GREEN logs. Tests cover unknown
digits, menu/absence, explicit unknown, omitted intervals, black ROI, fresh return,
source mismatch, invalid intervals and artifact roundtrip. Synthetic contexts do
not establish empirical detection accuracy on unreviewed video.

Development review completed on 10 September: all 1,247 prepared segment frames
are readable. Scoped current-code admission and remaining failures are documented
in [speed-visibility-results.md](archive/reliability/speed-visibility-results.md); this does not extend
visibility to complete laps or qualify Gate A.

The subsequent first complete BMW lap review and full-source replay are recorded in
[calibration-lap-results.md](archive/reliability/calibration-lap-results.md). One development calibration
is accepted; independent Gate A and metric spatial accuracy remain unqualified.

For the experimental first export, unverified visibility remains evidence to assess
locally, not an instruction to rerun a full review campaign. The report is allowed
before general qualification under [its explicit contract](specs/2026-09-13-session-coaching-report.md).
