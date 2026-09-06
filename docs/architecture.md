---
summary: current code boundaries, dependency flow, telemetry contract, and adapter responsibilities
read_when:
  - changing package boundaries or data flow
  - modifying extraction, normalization, domain, application, visualization, or adapters
---

# Architecture

## Data flow

```text
immutable video
  -> extraction observations
  -> normalization + quality/anomalies
  -> domain telemetry
  -> driving analysis
  -> CSV/HTML/API presentation
```

The dependency direction follows the arrows. Domain and normalization code do not import OpenCV, Plotly, or FastAPI.

## Boundaries

- `extraction`: frame I/O, HUD crops, color detection, OCR, minimap path and red-dot position.
- `normalization`: units, legacy CSV conversion, missing values, held/interpolated values, and anomaly labels.
- `domain`: immutable telemetry samples and quality vocabulary.
- `analysis`: position-aligned calculations and future coaching rules. It is intentionally small today.
- `application`: validated settings, component construction, and the sequential shared pipeline.
- `visualization`: DataFrame conversion, CSV export, Plotly reports, and summaries.
- `adapters`: argument parsing, filesystem choices, FastAPI requests, storage, and responses.

Root `main.py` and modules such as `src/video_processor.py` are compatibility entry points. New code imports `acc_telemetry.*` directly.

## Configuration

`config/roi_config.yaml` owns HUD geometry and profile-specific map detection. `config/telemetry.yaml` owns shared position, OCR recovery, and normalization thresholds. `load_settings()` validates both before the packaged CLI builds components.

## Telemetry contract

Legacy extraction records use `track_position` in percent for CSV compatibility. The domain converts it to `s` in `[0, 1]`. A value outside the expected range is retained and marked anomalous; it is never silently clipped.

Each field has one quality state: observed, missing, held, interpolated, predicted,
fused, or anomalous. The sample also preserves source values and anomaly reasons.
Longitudinal progress additionally carries its odometric and visual components,
uncertainty, source, and stable reasons. Lateral `d` is not present because video
evidence does not yet support it reliably.

In production, compatibility `track_position` is derived from available `s_fused *
100`. Only the explicit legacy tracker diagnostic remains map-only. Neither numeric
output alone proves spatial accuracy.

A1 resolves the audited lap integration gap: the generic pipeline reads one strict
fresh `FieldObservation` per lap label, while the explicit legacy path retains
smoothing/holding. Missing observations restart confirmation. Boundaries export
first-candidate, confirmation and last fresh previous-lap times; anchors remain at
confirmation. Sustained plausible OCR errors remain a limitation, and consensus is
not a calibrated probability. A2 preserves speed/gear/confirmed-lap quality in
`quality_hint` and reasons in CSV JSON `field_reasons`; normalization retains both.
`speed_raw`, `gear_raw` and `raw_lap_number` retain extraction evidence. Speed filtering
is unchanged, with median/recovery reasons exposed; production gear uses fresh
symbols and marks N/R unsupported. Modern numeric normalization rejects NaN/inf;
CSV nulls must be imported as empty strings or None (the CSV loader does this), not
pandas-inferred NaN. The comparison API now retains modern progress provenance and nullable controls. `TelemetrySample` is an available contract,
now an application result, but not yet the universal consumer boundary. See
`technical-audit-2026-09-05.md` before relying on field quality for analysis.

A3 adds reviewed `VisibilitySpan` inputs (see `control-visibility.md`). Generic
control decoding requires a reviewed span and a nonempty/nonblack ROI; missing
steering candidates remain unavailable. Quality and reasons reach CSV normalization.
TC/ABS remain unsupported. CLI and web metadata/report consumers handle null controls;
the explicit legacy extraction path retains its historical values.

A4 makes normalized samples and extraction frame observations available alongside
compatible records when explicit settings are supplied. The CLI and web service
provide those settings. `session_artifacts.py` writes and reloads `telemetry-v2`
with source/configuration/module hashes and exclusive atomic directory publication.
See `session-artifacts.md` for envelope contracts, optional adapter flags and the
separation between CFR/PTS checks and the still-pending independent reliability gate.

A5 delegates position alignment to pure `analysis/alignment.py`: temporal runs,
bounded interpolation, explicit channel quality and common-coverage deltas relative
to confirmed lap origins. Plotly masks gaps, and typed API responses preserve full
evidence. Legacy unqualified data remains diagnostic only. See
`comparison-reliability.md` for admission rules and absent frontend limitations.

A6 separates annotation preparation from measurement inference. `capture_annotations`
prepares unreviewed media and source manifests; pure `analysis/validation.py` validates
human labels/corpus readiness. `validation_config.py` owns independent thresholds.
Video preflight compares presentation packet PTS with decoded frames and profile
resolution; runtime decode status remains visible. See `capture-annotations.md` for
MOV discard-packet handling and the human-review gate that is still pending.

## Generic position estimation

The implemented estimator is generic across circuits using the static full-map HUD.
Its production wiring and representative clean/crash validation gates are complete.

```text
speed + delta time -> integrated distance -> s_odometry + uncertainty

static map -> unique centerline
red contours -> plausible dot candidates
centerline + candidates + odometry prediction -> s_visual

s_odometry + s_visual + confirmed lap boundary
  -> s_fused + source + uncertainty + reasons
  -> normalized domain telemetry
```

`s_odometry` integrates `speed_kmh / 3.6 * delta_time_s`. Completed clean laps are
normalized by their measured integrated distance; the median becomes an effective
lap-length calibration. Official circuit length is optional sanity evidence, not the
primary denominator.

The visual side first retains white pixels that recur in at least 60% of sampled
frames. It evaluates disconnected components independently and accepts exactly one
component whose pruned skeleton yields a sufficiently long closed cycle. This uses
the fixed HUD evidence without a circuit template or car-specific crop. The selected
cycle becomes a single centerline, not the external outline of the thick map stroke.
All plausible red-dot candidates are then retained, and odometric prediction plus
temporal continuity disambiguates nearby branches. A visual gap may be bridged briefly
with explicitly predicted/interpolated progress; long uncertain gaps become
unavailable.

Only a confirmed lap boundary may reset `s_fused` to zero. The opening partial lap is
unanchored unless offline evidence provides both trusted boundaries. The geometric
top-of-map start heuristic and unconditional forced completion are not part of the
target architecture.

## State and error handling

Frame extraction remains sequential because OCR recovery and lap observations depend
on history. `TelemetryPipeline` first collects raw evidence, then runs an offline pass
to confirm boundaries, calibrate measured lap distance, align the visual centerline,
and fuse progress. It owns video lifetime and closes the capture in a `finally` block.
CLI and web adapters construct the same application engine and do not duplicate fusion
rules.

`PositionTrackerV2` remains importable for compatibility and the legacy diagnostic,
but normal component construction does not instantiate it. Production CLI and web
paths use only `ProgressSessionEstimator` for longitudinal progress.

## Testing

Unit tests cover sampling, position direction and smoothing, OCR recovery, web profile propagation, configuration validation, pipeline closure, and normalization. The representative CSV fixture is synthetic and safe for Git. Full-video checks use ignored local session data.

## Planned coaching extension (not implemented)

`coaching-implementation-roadmap.md` links a reliability plan and a downstream
reference-corner dossier plan. The planned flow retains these package boundaries:
versioned observations -> normalized samples -> pure event/metric/comparison code ->
Markdown/JSON and paired cockpit media. Physical landmark annotations and a sourced
reference explanation are required for the first real dossier. ChatGPT receives
user-attached files; no LLM API integration or metric lateral estimator exists yet.
