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

Each field has one quality state: observed, missing, held, interpolated, or anomalous. The sample also preserves source values and anomaly reasons. Lateral `d` is not present because video evidence does not yet support it reliably.

## State and error handling

Frames remain sequential because OCR recovery, lap transitions, and position validation depend on history. `TelemetryPipeline` owns video lifetime and closes the capture in a `finally` block. Adapters choose inputs and outputs; they do not duplicate extraction rules.

## Testing

Unit tests cover sampling, position direction and smoothing, OCR recovery, web profile propagation, configuration validation, pipeline closure, and normalization. The representative CSV fixture is synthetic and safe for Git. Full-video checks use ignored local session data.
