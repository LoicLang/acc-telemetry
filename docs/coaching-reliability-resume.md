---
summary: accepted A6 authority and A7 resumption constraints after independent failures and autonomous visual reviews
read_when:
  - resuming coaching reliability validation
  - consuming accepted labels, holdout evidence or new agent reviews
---

# Reliability resumption

Read AGENTS.md, run `./scripts/docs-list`, then read `current-status.md` and its active
specification/plan. Current status owns the latest run and exact next action. Work
directly without subagents. User requests autonomous verification of reliable visual
evidence; do not request redundant reviews. Keep uncertain claims unavailable.

## A6 remains accepted

Base: `data/lab/coaching-reliability/run-007/processed/accepted-corpus-v4/index.json`.
Proof: `run-007/reports/a6-acceptance.json`. A6 is closed at `f060637`; do not reopen
its 100 readable frames per field, 20 degraded frames, 20 generic timed windows,
six physical passages or original recording lineage. `run-008/reports/input-integrity.json`
rehashes the source bytes and prior files. All original acceptance targets remain
unchanged. The new A7 association/gap/crossing definitions are separate additions.

Do not rerun the one-time A6 migration or generic consolidation over mixed approvals.
New reviews are separate files and derived copies; the accepted v4 tree is immutable.
User-approved annotations and agent visual reviews retain their respective reviewer
and source/image identities. Point approvals never become continuous visibility by
implication; A7's new visibility review has its own all-frame image evidence and
qualitative limitations. See `capture-validation.md` for the measurement contract.

## Semantics that must survive

- E16: reaches full throttle at **30397 / 506.616667 s**. Initial roughly 60% is
  approximate context, without a quantitative tolerance. Excluded from 5% latency;
  never relabel as an onset. Single-frame resolution is not zero timing uncertainty.
- E01/E12 remain untimed context. Other events retain original types. The two
  `first_visible_brake` markers and seven generic release starts do not establish
  applicable 5% crossings. Preserve their original types and publish exclusions;
  release latency stays not evaluated. Final onset/reapplication truth: 16 events
  in 15 windows.
- Physical passages track the checker-stripe near edge at fixed image coordinates,
  not axle crossings or metric position. Repeated normalized `s` dispersion cannot
  establish meter accuracy. Missing progress cannot be manufactured at a landmark.
- Downshift blips are displayed throttle, not inferred intentional input; E17's
  steering explanation remains a user hypothesis.
- Incident development clip packet lineage has +515 s original offset. BMW original
  and holdout lossless prefix retain verified identities. Holdout was reserved before
  inspection; do not tune the extractor on observed holdout failures.

## A7 execution

The validator now exists and consumes telemetry-v2 without OCR. RED and integration
regressions cover missing truth, shared bias, event association, confirmation delay,
field provenance, integrity rejection and incompatible fingerprints. Final real
speed measurements fail the unchanged targets. Pedal MAEs and scoped availability
pass; `capture-validation-results.md` records all denominators and uncertainties. The full historical replay detects
none of the five user-approved counter transitions. B remains blocked regardless
of subsequent visibility approvals.

Historical H01–H05 approval is scoped separately from the agent's exhaustive counter
review. Raw video remains immutable; the definition is a visible counter increment,
not the opening lap's clock reset or physical axle crossing. Relevant evidence and
current derived label versions are listed by `current-status.md`.

Finish any active artifact jobs before starting duplicate replays. Use the existing
`.venv`, FFmpeg and FFprobe. Run focused tests, the full suite, docs discovery and
`git diff --check` before each coherent commit. Update plan/handoff; push is authorized
on `codex/coaching-reliability`, no merge to main.
