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

The current legacy `track_position` remains map-only and is not reliable enough for
analysis. Diagnostic output may expose its raw projection and filtering decisions,
but must not be mistaken for validated domain `s`.

## Generic position estimation

The implemented estimator is generic across circuits using the static full-map HUD.
Its production wiring is complete; real-session validation gates remain open.

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

The visual side uses a single centerline, not the external outline of the thick map
stroke. It retains all plausible red-dot candidates and uses odometric prediction
plus temporal continuity to disambiguate nearby branches. A visual gap may be bridged
briefly with explicitly predicted/interpolated progress; long uncertain gaps become
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

## Testing

Unit tests cover sampling, position direction and smoothing, OCR recovery, web profile propagation, configuration validation, pipeline closure, and normalization. The representative CSV fixture is synthetic and safe for Git. Full-video checks use ignored local session data.
