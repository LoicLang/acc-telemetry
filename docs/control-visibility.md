---
summary: current video control visibility and missing-data semantics, with unsupported TC and ABS
read_when:
  - extracting controls with reviewed visibility annotations
  - preparing visibility.json for the annotation and artifact plans
  - interpreting missing controls in CLI or web outputs
---

# Reviewed control visibility

The default `reviewed` mode uses strict control observations. Without reviewed
spans, throttle, brake and steering remain missing, even if a decoder could return a
number. TC/ABS always remain missing with `indicator_semantics_unverified`; visibility
alone cannot establish whether an indicator means intervention or an aid setting.
The explicit legacy extraction wrappers retain their historical numerical behavior.

The explicit `automatic` measurement mode runs the same decoder without annotation
inputs; extracted values retain `hud_visibility_unverified`, rather than claiming a
review. Empty/black ROIs and missing steering candidates stay missing, TC/ABS remain
unsupported and pedal values are neither smoothed nor rescaled. Annotation files
are used only afterward to measure quality. This does not validate automatic HUD
presence; see `automatic-system-trial.md`.

Pass `--visibility-json PATH` to the CLI. The file is a JSON array, for example:

```json
[
  {"field": "throttle", "start_s": 10.0, "end_s": 12.0, "reviewer": "reviewer-id"},
  {"field": "brake", "start_s": 10.0, "end_s": 12.0, "reviewer": "reviewer-id"},
  {"field": "throttle", "start_s": 13.0, "end_s": 15.0, "reviewer": "reviewer-id"}
]
```

These are illustrative times, not reviewed annotations for any real capture.
Allowed fields are `throttle`, `brake`, `steering`. Times are relative to the input
video, start included and end excluded. Sort globally by start time; same-field spans
must not overlap. Reviewer must be nonempty. Nonfinite, reversed, empty, negative or
out-of-video intervals are rejected. The pipeline checks actual duration before
processing and closes the video even if validation fails.

Only declare spans after reviewing HUD readability. Split spans around overlays,
menus, occlusions or camera changes; omitted intervals are unavailable. The loader
validates structure, not the correctness of a review or its association with a source.
A4 stores the consumed spans alongside the source identity and configuration in
versioned artifacts; see `session-artifacts.md`. This does not validate the review.

Inside a reviewed span, an empty or entirely black ROI still refuses measurement.
Otherwise the existing pedal decoder is used, including zero for a released pedal.
A missing steering dot remains missing; a detected centered dot can be observed zero.
This is not an automatic HUD detector or a claim of independently measured accuracy.

The pipeline preserves control quality and reasons in CSV `quality_hint` and JSON
`field_reasons`. CSV blank values normalize to None. Summary aggregates with no
observations are null, including TC/ABS counts and percentages; partial indicator
percentages use only nonmissing samples. Local reports accept unavailable controls.

Web processing uses the same strict pipeline. Its Python service accepts an optional
`visibility_json` path; the HTTP upload/process forms do not yet expose annotations,
so their controls default to missing. Metadata preserves null averages. A5 makes the typed
comparison endpoint nullable and preserves provenance; it remains diagnostic only.
General reliability remains unqualified; this does not make it the next export task.

For new video metrics, retain those evidence boundaries and validate only the relevant
new capability. The [existing report contract](specs/2026-09-13-session-coaching-report.md)
remains useful for maintaining that consumer, not as the current product priority.
[Code audit](video-data-audit.md) · [Current status](current-status.md).
