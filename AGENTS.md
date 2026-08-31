# Working rules

## Scope

Keep the repository focused on ACC PS5 video telemetry. Do not add product features during cleanup or refactoring work.

## Architecture

Follow this dependency flow:

`raw capture -> extraction -> normalization -> domain -> analysis -> visualization`

CLI and web code are adapters. Shared behavior belongs in the application layer. Domain and normalization code must not depend on OpenCV, Plotly, or FastAPI.

## Data safety

- Treat every file under `data/**/raw/` as immutable.
- Never commit personal videos, full telemetry exports, OCR assets, or generated reports.
- Write derived output to `interim/`, `processed/`, or `reports/`.
- Never overwrite a source file. Verify size and SHA-256 before removing a migrated original.

## Changes

- Preserve current behavior unless the task explicitly changes it.
- Put thresholds in validated configuration, not scattered literals.
- Add or update a focused test before changing behavior.
- Run the focused tests and the full suite before each commit.
- Make one coherent change per descriptive commit. Do not mix file moves with behavior changes.

## Documentation

Keep `README.md`, `docs/architecture.md`, and `docs/acc-ps5-plan.md` aligned with the code. Archive historical material instead of deleting it unless active references and tests prove it obsolete.
