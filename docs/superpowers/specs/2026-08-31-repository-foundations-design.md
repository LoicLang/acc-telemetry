# ACC Telemetry Repository Foundations Design

## Objective

Turn the current ACC PS5 telemetry prototype into a clear, testable foundation for the future Road to Verstappen product without adding product features. The working repository will live at `/Users/loiclang/Documents/Projet/acc-telemetry` and retain its Git history.

## Baseline

The `fix/ps5-telemetry-calibration` branch is the implementation baseline because its 40 existing tests pass. The upstream `main` branch currently fails six position-tracking tests. The PS5 branch and the two existing design commits must remain traceable in history.

The GitHub repository `KubaC701/acc-telemetry` is a public upstream for which the current user has read-only access. It remains an upstream reference, not a writable delivery remote.

## Target boundaries

The code will be organized around this data flow:

```text
immutable capture
  -> video extraction and OCR
  -> normalization and quality assessment
  -> domain telemetry records
  -> driving analysis
  -> visualization and export
```

The command-line entry point and web API are adapters around the same application pipeline. They must not contain duplicate extraction or analysis rules.

### Package responsibilities

- `src/acc_telemetry/extraction/`: video frames, HUD regions, OCR, and raw observations.
- `src/acc_telemetry/normalization/`: stable units, missing values, anomaly flags, and conversion from observations to domain samples.
- `src/acc_telemetry/domain/`: typed telemetry concepts and session/lap semantics independent of OpenCV, web, and Plotly.
- `src/acc_telemetry/analysis/`: position-aligned comparisons and future coaching calculations; existing behavior only in this cleanup.
- `src/acc_telemetry/visualization/`: CSV/HTML output and plots.
- `src/acc_telemetry/application/`: orchestration shared by CLI and web adapters.
- `src/acc_telemetry/adapters/`: CLI and FastAPI integration.

Migration may use compatibility imports where required to keep behavior and commits reviewable. Large modules are split only when their existing responsibilities can be separated without changing algorithms.

## Telemetry contract

The normalized sample contract retains the useful current fields: frame, time, lap number, lap time, track position, speed, gear, throttle, brake, steering, TC activity, and ABS activity.

Track progress is named `s` in the domain model and is normalized over a lap. Import and export compatibility may retain `track_position` at system boundaries. Lateral distance `d` is explicitly reserved for a future extension and is not computed in this cleanup.

Every normalized value can carry quality information. The initial quality model distinguishes at least observed, missing, interpolated or held, and anomalous values. Existing extraction output is not silently rewritten: imperfect passages and rejected observations remain explainable.

## Configuration

Detection and validation thresholds used by the active PS5 path move into versioned YAML configuration grouped by responsibility:

- ROI geometry and HUD profile;
- color/OCR extraction thresholds;
- position tracking and map sampling;
- normalization and anomaly limits.

Defaults preserve current PS5 behavior. Configuration loading validates required keys, ranges, and types before video processing starts. Secrets and machine-specific paths do not belong in versioned configuration.

## Data policy

User recordings, full telemetry exports, debug frames, OCR data, and generated visualizations are local data and remain outside Git. Existing source data is never edited in place.

The repository documents these zones:

- `data/raw/`: immutable user-provided captures and source exports;
- `data/interim/`: reproducible extraction artifacts;
- `data/processed/`: normalized outputs and reports;
- `tests/fixtures/`: small, reviewed, non-sensitive test samples only.

A compact CSV fixture will be derived from the available ACC PS5 schema, with deliberately representative normal, missing, imperfect, and anomalous rows. It is test data, not a claimed real driving lap.

## Documentation

- `README.md`: project purpose, prerequisites, installation, one known-good command, tests, and output locations.
- `AGENTS.md`: short operational rules covering scope, architecture, data safety, tests, and commit discipline.
- `docs/product-context.md`: pilot/product loop and current ACC PS5 objective.
- `docs/architecture.md`: boundaries, dependencies, data flow, and telemetry contract.
- `docs/acc-ps5-plan.md`: current state, distance `s`, imperfect passages, quality/anomalies, and future lateral `d`.
- `CONTRIBUTING.md`: environment, conventions, tests, data rules, and atomic commits.

Historical documentation is retained under an archive or clearly marked as legacy when still useful. Files are deleted only after references and current behavior prove them obsolete.

## Testing and verification

The cleanup must preserve the 40-test green baseline. New focused tests cover configuration validation, the normalized telemetry contract, anomaly/quality representation, raw-data immutability expectations, and the representative CSV fixture.

Verification includes:

1. unit test discovery;
2. import/compile checks;
3. a quick-start smoke run that does not mutate source data;
4. checks for broken documentation links and tracked generated files;
5. a clean Git status after the final commit.

Large video integration checks use local files and are documented but not committed.

## Delivery and commit strategy

The repository relocation preserves history and leaves the old temporary worktrees untouched until the new repository is verified. Changes are committed in reviewable units: repository skeleton and policies, package boundaries, configuration/domain contract, fixture/tests, documentation, and verified legacy cleanup.

No commit will mix broad file movement with behavior changes. No feature beyond repository hygiene, configuration, quality representation, and architecture separation is included.

## Acceptance criteria

- The autonomous repository exists at `/Users/loiclang/Documents/Projet/acc-telemetry` with retained history.
- The PS5-tested branch is the cleanup baseline and all pre-existing tests remain green.
- Extraction, normalization, domain, analysis, visualization, application, and adapters have explicit boundaries.
- The README provides a working quick start and `AGENTS.md` is concise and operational.
- Product, architecture, contribution, and ACC PS5 plan documents match the implemented code.
- Distance `s`, imperfect passages, quality/anomalies, and future `d` are documented and represented without inventing lateral telemetry.
- Active thresholds are configurable and validated.
- Raw data is ignored, treated as immutable, and never modified by tests or normal processing.
- A compact representative CSV fixture supports focused tests.
- Dead code is only removed or archived with evidence that active imports, entry points, tests, and documentation no longer depend on it.
- The final worktree is clean and the work is split into descriptive atomic commits.
