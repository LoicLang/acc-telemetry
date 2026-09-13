---
summary: single handoff for the approved first experimental session_coaching.md export
read_when:
  - starting any repository task
  - deciding the next action or the active delivery scope
---

# Current status

Last verified: **2026-09-13**. Branch: `codex/coaching-reliability`.
Push authorized; no merge to main. No sub-agents or exhaustive counter review.
Owner policy13 September: autonomous implementation choices and proportionate checks
per `AGENTS.md`; no mandatory full suite per commit or tests for trivial documentation.
This policy edit was reviewed by diff; the historical test results below were not rerun.

## One active objective

Produce **one real, autonomous `session_coaching.md`** from an existing local session,
so the driver can attach it to GPT for a supported training priority and exercises.
The exporter supplies facts, comparisons, reviewed visual descriptions and limits;
GPT supplies hypotheses/exercises. No web service or GPT API integration.

Active plan: `plans/2026-09-13-first-gpt-export.md`
Active specification: `specs/2026-09-13-session-coaching-report.md`

The owner adopted this smaller milestone on 13 September and requested documentation
cleanup. That cleanup is complete; **the report exporter is not implemented yet**.
The next implementation task follows the four lots below, not another planning phase.

## Explicit scope decision

**Gate A: FAIL. `coaching_eligible=false`.** Targets and existing artifact flags stay
unchanged. The owner expressly authorizes the limited experimental export **without
first passing all of Gate A**. This replaces the old rule that blocked every report
behind complete qualification, a professional reference and the full seven-metric dossier.

Use or exclude each fact according to its actual local evidence. `observed` is not
`verified`; a reason such as `hud_visibility_unverified` must affect its admissibility.
A duration needs evidence across its relevant interval, not just two correct endpoints.
No unsupported fine trajectory diagnosis, invented visibility, zero replacement or
certain causal inference. General reliability and validated automated coaching remain
blocked. A professional reference and next-session improvement are later milestones.

## Verified starting material

All paths below are repository-relative, under ignored `data/lab/coaching-reliability/`:

- **Session:** `run-024/processed/crash-session/` — load with `read_session_artifacts()`.
  Its four files are manifest, observations, normalized samples and telemetry CSV.
- **Measurements:** `run-024/reports/results.json`, `annotated-validation.json` and
  `final-verification.json`; existing display: `run-024/reports/index.html`.
- **Frozen counter truth:** `run-022/processed/crash-fixed-roi-labels.jsonl` and
  `run-022/reports/crash-numeric-truth.json`. No repeat visual annotation is needed.
- **Report-reading trial:** `run-025/reports/essai-gpt/ESSAI_COACHING.md`, `preuves.json`
  and images; additional approach frames: `run-025/reports/incident-context/`.
  This is a manual provisional analysis, not the promised generated session report.

The manifest identifies source `data/lab/2026-09-03-generic-s-fusion/crash-representative.mov`,
SHA-256 `b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124`,453613415 bytes.
All 29,402 presented frames were processed in native 1920×1080 exactly 60 fps CFR.
Times are relative to that input clip; do not infer a different original-video origin.
Artifacts and supporting paths were rechecked during this cleanup.

| Fact | Scope |
| --- | --- |
| Speed available29,298/29,402 (99.65%) | Availability, not accuracy |
| Brake/throttle available29,402/29,402 | Does not prove HUD visibility |
| Speed exact21/21 annotated points | No numerical truth between those points |
| Pedal MAE brake1.60/gas3.12 points; maximum 5.88 |21 points per field |
| Counter29,402 fresh exact values;4/4 transitions | Frozen run-022 comparison, not physical crossing truth |
| Estimated `s` available26,844 frames | Spatial accuracy unverified; use physical landmarks for comparison |

Known limitations: full throttle often reads 94.12%; released pedals can leave
0.65–1.70%; blips may be automatic; true39km/h at impact is rejected; V-CRASH-15
has28/31 available speed frames. Keep these facts, do not tune them away for this export.

The actual clip shows a **McLaren 720S GT3 family** cockpit; original/EVO and hardware
remain unconfirmed. The ending of Les Combes/Malmedy is a candidate zone. Precise
landmarks and two/three comparable passages remain to be selected. Do not substitute
BMW/Bruxelles from another capture. Include the approach to an incident: the old
347–352s excerpt already starts off track. Conditions/setup can remain explicitly unknown.

## Implementation and stop condition

Existing: shared automatic pipeline, typed measurements, integrity-checked artifacts,
validation, local CSV/HTML. Proposed, **not yet present**:
`analysis/session_summary.py`, `application/session_report.py`, `adapters/session_report.py`.

1. Freeze/reload the existing session and select comparable passages.
2. Calculate only locally supported facts needed for a training subject.
3. Generate `session_coaching.md` with a reproducible local command.
4. Read it without repository/history, test it with GPT and fix precise missing evidence.

Stop this milestone when the real file is autonomous and supports an evidenced exercise.
No mandatory seven-metric implementation, new capture, professional reference, web work,
full OCR replay, perfect `s`, or measured next-session improvement before that delivery.
Private/generated outputs stay ignored. Old reports/designs are evidence in
[the archive](archive/README.md), never competing instructions.

## Verification and exact next action

Runtime code/configuration are unchanged by this documentation cleanup. Prior run-024
artifacts and referenced evidence are preserved.16 focused and324 full-suite tests pass;
link/routing checks pass. All verification results are
recorded in `data/lab/coaching-reliability/docs-cleanup-2026-09-13/reports/`.

**Next action: execute lot 1 of the active plan — load and integrity-check
`run-024/processed/crash-session/`, then write a source-bound local selection sheet for
two or three comparable passages with reviewed entry/exit landmarks and incident context.**
