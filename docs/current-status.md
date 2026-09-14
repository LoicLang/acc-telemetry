---
summary: perception-system handoff after the first export; next full-lap temporal prototype and PC-supervised spatial feasibility
read_when:
  - starting any repository task
  - locating the delivered file or reproducing it
  - deciding the next action and remaining evidence limits
---

# Current status

Last verified: **2026-09-14**. Branch: `codex/coaching-reliability`.
Push authorized, no merge. No sub-agents or exhaustive counter review.

## Active objective — the AI's eyes, not a coaching-rule engine

Owner clarification14 September: the software must expose what happened across the
whole session, with scene, controls, timing and placement. The consuming AI analyses
weaknesses and proposes training. The first text export is a completed intermediate
step, not the final perception system. Single evolving [active plan](plans/2026-09-13-first-gpt-export.md).

Next milestones: M1 full-lap temporal coverage; M2 synchronized PC video/position
labels and track geometry; M3 image/temporal d model and PS5 transfer evaluation;
M4 global multimodal perception package; M5 factual reconstruction test by the AI.
The spatial component is now a first-class feasibility objective, not permanently
excluded. No dataset/model or new perception module has been built in this planning turn.

PC live capture access is unconfirmed. `d` must be derived from position plus a stable
track frame, not from an expert's lap alone. Metric truth/units, synchronization and
PC→PS5 transfer remain to establish. M1 can proceed with existing source/artifacts
while these prerequisites are prepared. Professional reference and PC training labels
serve different roles. Gate A FAIL and `coaching_eligible=false` stay unchanged.

## Ready for tonight —14 September

Start M1 on **HUD lap4 of run-024**, frames19–8784 inclusive, source interval
[0.316667,146.416667) s between confirmed counter boundaries. The source, session
artifacts and run-026 case/report paths were checked present; no OCR or model run.
These are counter-defined bounds, not certified physical crossings/legal-lap evidence.

Tonight's concrete output: one complete-lap timeline, source-bound zone/action index,
and one detailed synchronized scene/control window. Use a new ignored output folder
(e.g. run-027 if still free). Existing Combes imagery can bootstrap the detail window;
do not restrict the overview to that zone. Follow the practical M1 subsection in the
active plan. Tests are proportionate to the actual changes.

M2 needs ACC Windows access, simultaneous video/telemetry recording and a usable
track-geometry source. Access, car variant, camera/FOV and hardware remain unknown.
Confirm them when possible, but do not block M1 or start paid services/training.
This update prepares the handoff only: M1–M5 implementation has not started.

## Delivered result

**The first real `session_coaching.md` is generated and locally reviewed.**
It is a standalone French evidence dossier from the owner's actual run-024 session:
three passages, shared physical landmarks, 22 locally reviewed speed readings,
approximate transit times, approach/incident context and a request to GPT.
The exporter supplies facts and limits; GPT proposes hypotheses and exercises.

Active plan: [perception milestones](plans/2026-09-13-first-gpt-export.md).
Implemented first-export contract: [session report](specs/2026-09-13-session-coaching-report.md).
Lots 1–3 and the local reading review are done. **A fresh GPT conversation has not
been tested.** The user's delivery instruction expressly distinguishes these checks;
that remaining trial does not prevent delivery of the file.

## File and reproduction

Private/generated files remain ignored under `data/lab/coaching-reliability/`:

- **Deliverable:** `run-026/reports/session_coaching.md`.
- **Source-bound selection:** `run-026/interim/case.json`; referenced review images
  must remain available. 91 source images reviewed, including eight reused from
  `run-025/reports/incident-context/`; new local scene decoding only, no OCR replay.
- **Integrity:** `run-026/reports/integrity.json` (payload/envelope check via
  `read_session_artifacts()`, source size/SHA-256 verified; unchanged CFR proof reused).
- **Reading verdict:** `run-026/reports/relecture.md`, same assistant and task,
  constrained to the file's facts; not blind, independent or driver-validated.
- **Checks:** `run-026/reports/tests.txt`, `verification.json`, `command.txt`.

From repository root, choose a new output directory (existing files are refused):

```bash
PYTHONPATH=src .venv/bin/python -m acc_telemetry.adapters.session_report \
  --session data/lab/coaching-reliability/run-024/processed/crash-session \
  --case data/lab/coaching-reliability/run-026/interim/case.json \
  --output data/lab/coaching-reliability/run-026/reports/reproduction-02/session_coaching.md
```

Reproduction needs only the existing artifacts, case and its image/supporting evidence;
it does not decode video, run OCR or call GPT. The source clip is unchanged. SHA-256:
`b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124`, 453613415 bytes.
The 29,402 presented frames are native 1920×1080 exactly 60 fps CFR. Source times are
relative to that clip, not a guessed origin in a larger recording.

## What the file establishes

Spa, McLaren 720S GT3 family cockpit, original/EVO unknown. The shared zone is the
left/right transition after the first right of Les Combes toward Malmedy. A/B refer
to the disappearing ends of the first/final inside right curbs, reviewed in 0.5 s
windows. Perspective/lateral-position error is unquantified: no exact timing plane.

| Passage | Preserved window | A | B | Approximate A→B | Reviewed outcome |
| --- | --- | --- | --- | --- | --- |
| P1, HUD lap 4 | 39–57 s | 45–45.5 s | 51–51.5 s | 5.5–6.5 s | Continues on visible roadway; four-wheel legality unverified |
| P2, HUD lap 5 | 185–204 s | 191.5–192 s | 200–200.5 s | 8–9 s | Slows in/after left, approaches inside runoff/rail before final right |
| P3, HUD lap 6 | 334–352 s | 339.5–340 s | 345.5–346 s | 5.5–6.5 s | Goes into left gravel after B, then reorients toward barriers |

Speeds near A are close (six reviewed readings 110–114 km/h). The later outcomes
differ: this supports a local repeatability exercise, not a certain common cause.
P1/P3 transit similarity does not mean equally successful exits; the aftermath is
retained. P2 is not included in clean-passage statistics. No perfect reference exists.

## Trust boundary, unchanged

**Gate A: FAIL. `coaching_eligible=false`.** Owner authorized this limited export
before general qualification. Targets, original annotations and artifact flags are
unchanged. Historical manifest `gate_a=not_evaluated` is distinguished from the
run-024 final verification's FAIL; neither is silently rewritten.

Availability remains 29,298/29,402 speeds, all pedals, 26,844 estimated s values;
availability is not accuracy. Existing 21-point speed/control checks and frozen
run-022 counter comparison are reused, not generalized to all frames. New point
reviews supplement, never overwrite, the old annotations. A speed is admitted only
when observed and equal to the reviewed HUD reading; nulls and reasons persist.

No continuous pedal metrics or minimum speeds are published. Full gas often reads
94.12%, released pedals 0.65–1.70%, blips can be automatic; true 39 km/h at impact was
rejected, V-CRASH-15 has 28/31 speeds. No diagnosis of steering/TC/ABS or certain
causality. Hardware, exact conditions/setup and driver feel remain unknown. Estimated
s is not used for alignment. General reliability and validated automated coaching remain unqualified. The new
perception plan explicitly evaluates temporal detail and spatial estimation; a
professional reference and next-session improvement are separate from that measurement.

## Implementation and verification

Implemented `analysis/session_summary.py` (pure admission/coverage/bounded times),
`application/session_report.py` (artifact/case/evidence reading and atomic text
publication), and thin `adapters/session_report.py`. No extraction/pipeline changes.
Case schema and constraints are documented in the active specification.

Focused report and existing artifact tests: **28 pass**. Report-specific tests cover
source/manifest mismatch, null/held/anomalous/discordant speeds, missing landmark
reasons, interval review gaps, bounds, units/source origin, image integrity and
exclusive publication (including a concurrent writer). Real reproduction is byte-identical.
No full-suite rerun: this is an isolated downstream consumer. Existing Pydantic
configuration deprecation warning remains unrelated. Documentation reviewed and
listed with `./scripts/docs-list`.

## Exact next action

**Resume M1 tonight: load the existing run-024 session, select frames19–8784 and
produce the full-lap timeline plus a first synchronized scene/control window.**
Then extend zone/action indexing and temporal detail under the active plan. Prepare
ACC PC access/labels/geometry for M2 independently of this local work. No new OCR,
exhaustive counter review or coaching diagnosis is needed to begin.

Documentation-only handoff update: relevant paths/bounds checked, text/links/diff
reviewed; no automated test suite or video processing was needed for this update.
