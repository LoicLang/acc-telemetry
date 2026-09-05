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

The September 5 audit confirms integration gaps: lap observations arrive prefiltered
and held, speed quality is passed to fusion but lost in records, and the comparison
API omits modern progress provenance. `TelemetrySample` is an available contract,
not yet the universal application/consumer boundary. See
`technical-audit-2026-09-05.md` before relying on field quality for analysis.

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
