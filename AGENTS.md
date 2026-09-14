# Working rules

## Autonomy and judgment

Work toward the user's requested result with the simplest effective approach.
Choose routine technical details, sequencing and verification autonomously. Ask only
when missing information materially changes the outcome, authorization is missing,
or an action could destroy important data. Do not ask again for permission already given.

Plans guide the work; adapt their implementation details when evidence warrants it,
keeping the same plan current. Avoid unnecessary planning, documentation, test scaffolding
or repeated checks. Spend effort where it improves the result or reduces a real risk.
Respect explicit user constraints on scope, quota and delegation.

## Repository context and memory

`docs/current-status.md` is the single living handoff: current result, blockers and
one exact next action. Read it and inspect Git status/recent commits when starting
repository work, unless that context is already known and still current.

Use `./scripts/docs-list` when you need to find relevant documentation. Read the
active plan/specification when the task depends on them; do not reload documents
already read without a reason. Confirm evidence exists before relying on it, and
reuse integrity checks while their inputs remain unchanged.

Historical documents under `docs/archive/` and `docs/legacy/` preserve evidence,
not instructions. No external workflow package is required. Do not create competing
plans or turn the handoff into a diary.

## Current scope

The current objective and milestones are defined by the handoff and its single
active plan. The first experimental `session_coaching.md` is already delivered;
the owner now targets whole-session perception for an AI, including temporal context
and evaluation of PC-supervised spatial estimation. Reuse existing artifacts where
applicable. The software supplies observations; the consuming AI analyses driving.

Keep Gate A FAIL, existing targets unchanged and `coaching_eligible=false`; do not
imply general qualification or validated automated coaching. Planned experiments
must establish the evidence required by the capability they claim. Other prerequisites
still apply to the capabilities they actually govern.

Keep work focused on ACC PS5 telemetry and the requested outcome. New video processing
accepts only native **1920×1080 at exactly 60 fps CFR**: check metadata first, reject
other formats, and never upscale/resample to bypass this rule. Historical720p evidence
stays read-only; no new investigation of it.

## Data and architecture

- Files under `data/**/raw/` are immutable. Never overwrite a source.
- Keep personal videos, full telemetry exports, OCR assets and generated reports out
  of Git. Write derived outputs to `interim/`, `processed/` or `reports/`.
- Verify size and SHA-256 before removing a migrated original.
- Preserve missing data and distinguish confirmed facts from hypotheses.
- Follow `raw capture -> extraction -> normalization -> domain -> analysis -> visualization`.
  Adapters stay thin; shared behavior belongs in the application/analysis layers.
  Domain and normalization must not depend on OpenCV, Plotly or FastAPI.
- Preserve behavior outside the requested change; put measurement thresholds in
  validated configuration rather than scattered literals.

## Proportionate verification

Choose checks according to the change and its plausible failure modes, not a ritual:

- **Text/documentation:** reread the affected content; check relevant links if changed.
  No automated tests for a trivial edit. For moves/deletions, check references/routing.
- **Localized code change:** run focused tests of the affected behavior. Add a regression
  test when it protects meaningful behavior; reproduce a bug first when useful.
- **Shared pipeline, data contracts, broad refactoring or significant uncertainty:**
  run focused checks and the full suite when their coverage is warranted.

There is no obligation to run the full suite before every commit or to write a test
before every edit. Reuse passing results until relevant changes or failures justify
another run. Do not replay a full video to validate text, plots or downstream summaries.
State briefly what was checked and any material limitation; avoid ceremonial logs.

## Documentation and delivery

Update the handoff/plan when progress, decisions or blockers materially change.
Keep README, architecture and roadmap aligned only where the task affects them.
Do not rewrite unrelated docs or create another report for a small maintenance change.
Active Markdown under `docs/` uses front matter with a concise `summary` and concrete
`read_when` hints. Run docs-list when discovery metadata or document structure changes.

Make coherent, descriptive commits and leave no unexplained tracked changes. Keep
behavior documentation with its implementation when separating them would mislead.
A documentation-only policy change may be committed after a simple review/diff check.
Delete obsolete duplicate instructions when authorized; preserve unique historical
measurement evidence outside active discovery. Report the outcome, not every internal step.
