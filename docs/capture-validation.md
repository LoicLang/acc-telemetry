---
summary: existing general validation contract and its separation from the authorized experimental text export
read_when:
  - running independent capture validation or interpreting gate-a.json
  - changing field, event, coverage or landmark measurement definitions
---

# Independent capture validation

`scripts/validate_capture.py` reads existing telemetry-v2 artifacts through the A4
integrity-checking reader. It never invokes OCR, FFprobe or the extractor. Source
identity, profile, ordered frames and timestamps are checked against independent A6
capture evidence. Additional historical/clean preflight is performed separately.

```bash
PYTHONPATH=src .venv/bin/python scripts/validate_capture.py \
  --artifacts PATH_TO_SESSION \
  --annotations PATH_TO_LABELS_JSON \
  --capture PATH_TO_CAPTURE_JSON \
  --output NEW_REPORT_JSON
```

`--capture` defaults to `capture.json` beside the labels. Output is a new JSON file;
existing files, source paths and `raw/` destinations are refused. Reports and videos
stay in ignored `data/lab/`. The application owns orchestration in
`application/capture_validation.py`; pure metrics live in `analysis/validation.py`.

## Definitions and denominators

- **Field accuracy:** exact annotated frames, fresh extraction observation and fresh
  normalized sample both required. Raw absolute errors, MAE and linearly interpolated
  P95 use measured pairs only. Missing/held/anomalous values count as abstentions in
  point coverage. Reports include individual frame/value/error pairs, excluded labels
  and annotation tolerances. Tolerances are published, never subtracted from errors.
- **Reviewed absence:** a fresh measurement at an explicitly invisible HUD frame is
  an accuracy failure. Unknown visibility is neither absence nor readability.
- **Segment coverage:** fresh output availability over explicit `evaluation_segments`
  (inclusive frame intervals), or over reviewed visibility spans when target segments
  are absent. Segment selection defines a denominator, not visibility truth. Control
  extraction still requires separately reviewed visibility. No segment or span means
  `not_evaluated`; a few accepted points never imply continuous coverage. These short
  target segments do not establish full-lap coverage.
- **Lap events:** first fresh candidate time against the midpoint of a reviewed
  counter-transition interval. Maximum-cardinality chronological one-to-one matching,
  then minimum total absolute distance. Duplicates, missed truth and predictions
  outside the association window are separate. Confirmation delay is measured from
  first candidate to confirmation; it is not the passage error. Sparse truth cannot
  qualify unmatched predictions as false positives. A missed approved event already
  establishes failure; a pass requires an exhaustive transition review.
- **Pedal latency:** first consecutive fresh observation crossing 5%, with a maximum
  inter-frame gap of 0.10 s. Missing/held observations break the sequence. Matching
  occurs separately by source and subtype. Detections beyond sparse review scope are
  counted separately, not called false positives. Fully observable windows with no
  crossing fail; unannotated nearby crossings are not automatically false positives.
  A generic release start is excluded unless a falling threshold crossing is explicitly
  reviewed. Absent visibility evidence remains `not_evaluated`. This is not the
  future B4 sustained coaching-event detector.
- **Annotation uncertainty:** midpoint error and interval half-width are distinct.
  Unknown human timing uncertainty stays null, including a single-frame marker.
- **Physical landmarks:** use normalized `s` at the interval's central frame; publish
  its time offset, all available interval values, quality and uncalibrated estimator
  uncertainty. Repeated-passage dispersion is the shortest circular covering arc.
  It is never an absolute error or a distance in meters. Fewer than two available
  passages leave dispersion `not_evaluated`.

A6 E16 remains `throttle_reaches_full`, frame 30397, excluded from the 5% metric.
Its approximate initial 60% remains context, without an invented numeric tolerance.
The two `first_visible_brake` markers also lack reviewed 5% semantics and are excluded.
Seven generic release starts show filled bars and do not establish falling 5% truth;
those annotations remain intact while release latency stays `not_evaluated`.
No old marker, approval, lineage or holdout role is relabelled by validation.

All original `config/validation.yaml` targets remain unchanged. A7 adds explicit
measurement definitions: 1.0 s association window (distinct from the unchanged
0.10 s error target), 0.10 s fresh-observation gap, and 5% crossing. These definitions
were fixed before the capture results. A6 acceptance retains its original config hash.

## Reviews and integrity

User-approved point/event labels and agent reviews have separate provenance. At the
user's explicit request, A7 can independently review clear visual evidence itself;
this does not turn that review into a user approval. Visibility rows preserve their
own reviewer rather than inheriting the annotator of old point labels. Temporal
min/max contact sheets include every frame but do not preserve temporal ordering;
they support a qualitative fixed-HUD visibility review, not numeric pedal accuracy.
Ambiguous evidence must remain unreviewed.

The fingerprint includes the extractor, pipeline/components/config, progress,
lap-state, odometry, normalization, domain and artifact-writer module hashes, resolved
configuration, profile, validation settings and measurement-module hashes. A global
Git hash is retained for traceability but documentation-only commits do not invalidate
compatibility. Reviewed visibility is an evidence input, not extractor tuning.
Holdout extractor/settings compatibility is checked against its pre-inspection
reservation. Do not fit an extractor correction to holdout failures.

`gate-a.json` requires six checks: software regressions, lap events, field accuracy,
field coverage, timebase and holdout. Missing checks cannot pass; all six must pass
with a compatible fingerprint before coaching admission. An available failed metric
is not hidden by other missing evidence. Unsupported TC/ABS, steering accuracy and
metric spatial accuracy remain excluded from coaching capabilities.

`scripts/diagnose_progress.py` preserves old counters with
`metric_scope: internal_consistency_only` and `spatial_accuracy: not_evaluated`.
Identically biased curves can have zero checkpoint spread; this is a regression test,
not independent spatial evidence. Final run-008 results and limitations are in `archive/reliability/capture-validation-results.md`;
`current-status.md` owns the live next action.

## Experimental report boundary — owner decision13 September2026

The six-check gate above remains the general qualification contract; its code/targets
and `coaching_eligible=false` are unchanged. The first experimental `session_coaching.md`
is explicitly allowed before the full gate passes. It retains local admissibility,
nulls, reasons and uncertainty without certifying the session. Do not start a new
holdout/corpus campaign as its prerequisite. See [the report contract](specs/2026-09-13-session-coaching-report.md).
