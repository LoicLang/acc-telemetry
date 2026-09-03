# Working rules

## Durable repository memory

Chat history is short-term context. The repository is the durable source of truth.
A new agent must be able to understand the current state, active work, blockers, and
next action from the tracked documentation and recent Git history alone.

`docs/current-status.md` is the single living handoff document. Keep detailed,
long-lived guidance in focused documents under `docs/`; do not turn this file into
a project diary.

## Start every repository task

Before changing code, tests, configuration, or active documentation:

1. Read this file.
2. Run `./scripts/docs-list`.
3. Always read `docs/current-status.md`.
4. Use the index `read_when` hints to select the other relevant documents.
5. Read the active specification and dated plan named by `docs/current-status.md`
   when the task affects that milestone.
6. Inspect `git status --short --branch` and recent commits.
7. Confirm that local evidence referenced by a document exists before relying on it.

Do not load every historical Markdown file by default. `docs/legacy/`,
`docs/archive/`, and `docs/superpowers/` contain history or working material and are
excluded from normal discovery.

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
- Keep active-plan checkboxes synchronized with completed work.
- Record confirmed facts separately from hypotheses.
- Do not start a downstream feature while its prerequisite stage gate is failing.

## Documentation

Keep `README.md`, `docs/architecture.md`, and `docs/acc-ps5-plan.md` aligned with the code. Archive historical material instead of deleting it unless active references and tests prove it obsolete.

Every active Markdown document under `docs/` must begin with:

```yaml
---
summary: concise description of the document's authority and contents
read_when:
  - concrete situation in which an agent must read it
---
```

Before stopping work:

- update `docs/current-status.md` with completed work, current work, blockers,
  verification evidence, and one exact next action;
- update `docs/acc-ps5-plan.md` only when product direction or a stage gate changes;
- update the active dated plan checkboxes when plan execution advances;
- run `./scripts/docs-list` and the appropriate tests;
- make atomic commits and leave no unexplained tracked changes.

Documentation describing a behavior change belongs in the same commit when a
separate commit would leave repository truth temporarily misleading. Standalone
planning or policy decisions receive their own documentation-only commit.
