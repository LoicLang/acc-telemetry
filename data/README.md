# Local training data

This directory is the durable local home for ACC training sessions. Personal artifacts are intentionally ignored by Git.

## Session layout

```text
data/
  catalog.csv
  sessions/
    YYYY/
      YYYY-MM-DD_track_platform_purpose/
        session.yaml
        raw/
        interim/
        processed/
        reports/
  lab/
  shared/
```

- `raw/`: original videos and source exports. Files are immutable after ingestion.
- `interim/`: repeatable extraction results and calibration artifacts.
- `processed/`: normalized telemetry used for comparison and coaching.
- `reports/`: generated HTML, images, and session analysis.
- `lab/`: smoke tests, failed extractions, and experiments that are not pilot sessions.
- `shared/`: reusable local resources such as OCR language data.
- `catalog.csv`: local artifact index with session, role, relative path, SHA-256, byte size, and legacy source paths.

## Naming

Use `YYYY-MM-DD_track_platform_purpose` for session folders. Unknown metadata belongs in `session.yaml` as `null`; do not guess a car, setup, weather, or session type.

## Safety

Processing must never modify a file in `raw/`. Derived files go to the other zones. Before deleting a migrated original, verify that destination size and SHA-256 match and that the old path is recorded in the catalog.
