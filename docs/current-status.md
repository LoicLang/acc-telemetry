---
summary: local perception works on one case; next bounded whole-session condensation for recurring difficulties
read_when:
  - starting repository work or opening the current perception result
  - continuing temporal coverage or preparing PC-supervised spatial data
---

# Current status

Last verified: **2026-09-14**. Branch `codex/coaching-reliability`.
Push authorized, no merge. No sub-agents or exhaustive counter review.
Use proportionate checks under AGENTS.md; do not rerun OCR to change reports.

## Objective and active work

Build the AI's eyes: whole-session scene, controls, timing and placement with honest
coverage/uncertainty. The consuming AI analyses weaknesses and proposes training;
the software indexes neutral observations, not driving faults.
The main model must receive a compact whole-session representation, not tens of
minutes of 60 fps video. Local extraction/perception carries that volume; the output
must expose recurring difficulties and defensible performance gaps under a bounded
reading budget. This central condensation capability is still missing.

Active plan: `plans/2026-09-13-first-gpt-export.md` (M1–M5 perception milestones).
Implemented M1 contract: [perception package](perception-package.md).
The earlier [text-export contract](specs/2026-09-13-session-coaching-report.md) remains
implemented, but a single text dossier is not the final perception system.

The owner authorized starting local work while preparing a new driving video in about
an hour. **M1's first full-lap prototype is now delivered.** M2/PC is not ready: the
software/service used to run ACC on the Mac and the available time window are still
unknown. Ask for those facts before starting any timed PC environment; continue M1
independently. No PC session, dataset or model training has been launched.

## Open the actual result

Private output: `data/lab/coaching-reliability/run-027/reports/lap-4/index.html`.
The localhost-only preview at `http://127.0.0.1:8767/` is intentionally left running
for the user. It supports video seeking and is confined to the generated package.
See the M1 contract for the reproducible export/preview commands; output directories
must be new. Keep the package together so its relative media links resolve.

The package includes a full video, all samples/qualities/reasons,14 contiguous zones,
95 neutral event candidates, an18s detail clip,21 native images at0.1s and four sheets.
Choose any zone/event, seek from a curve, or step one video frame. The values/cursor
use the presented video-frame timestamp when available; fallback is labeled approximate.
No reconstructed lateral trajectory or steering-angle claim is present.

Scope: HUD lap4, frames19–8784 inclusive, source interval
[0.316667,146.416667) s —8766 presented frames. These are confirmed-counter bounds,
not certified physical crossings or a legal-lap claim. The14 navigation-zone windows
were coarsely reviewed from30 source views; no exact apex/entry/exit inference.
Detail video39–57s; dense sequence49–51s. This does not constitute full-session visual
coverage or a fresh-model test of every transition.

## Inputs, provenance and limits

- Frozen session: `run-024/processed/crash-session/`, read through `read_session_artifacts()`.
- Source: `data/lab/2026-09-03-generic-s-fusion/crash-representative.mov`,453613415 bytes,
  SHA-256 `b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124`.
- M1 zone input: `run-027/interim/zones.json`, source-bound with review/image hashes.
- Results/command/tests: `run-027/reports/`, detailed contract above.
- Existing first dossier: `run-026/reports/session_coaching.md` and
  `run-026/interim/case.json`; retain as prior evidence, not a global diagnosis.
- Complete frozen counter truth: run-022; no new counter review needed.

Run paths without `data/` above are relative to ignored `data/lab/coaching-reliability/`.
Native1920×1080 exactly60fps CFR source and rendered media checked. Whole-lap and detail
media contain8766/1080 presented frames. No extraction/OCR replay, new speed truth or
pedal smoothing. New config/perception.yaml controls only neutral event indexing.

This lap:8757 fresh speed values,8766 per pedal,8764 gear values.12 brake-on/12 brake-off,
13 throttle-on/13 throttle-off,44 gear-change candidates plus initial active throttle.
A candidate can reflect a blip or misread; it is not a verified driver intention.
All quality reasons persist.95 event candidates do not mean95 qualified actions.

**Gate A FAIL; coaching_eligible=false.** Global accuracy, automatic HUD recognition,
steering angle, d and PS5 spatial precision remain unqualified. Full throttle often
reads94.12%, small pedal residues remain, and some speed readings abstain. No causes,
ideal line, skill scores or exercises are produced by this package.

## Implementation and verification

New pure `analysis/perception.py`, orchestrator `application/perception.py`, renderer
`visualization/perception.py`, CLI `adapters/perception.py` and optional read-only
`adapters/perception_preview.py`. Existing extraction/pipeline modules unchanged.
The exporter validates inputs, renders frame-bounded native clips, preserves samples,
and publishes a complete new directory exclusively. A failed render cleans staging.

45 focused tests pass: event/gap semantics, complete partition, media/frame bounds,
input/output protection, HTML data safety, HTTP Range and existing artifact/report
regressions. No full-suite rerun for these isolated consumers. Runtime browser checks
confirmed source39s/frame2340, source49s/frame2940 then2941, and another zone (Pouhon)
at72s/frame4320 with live playback. Direct file:// navigation was unavailable to the
browser tool; the allowed localhost preview was verified. It required proper Range
support, now included. No source or prior artifact was modified.

## Exact next action

**Prototype the zone × passage index and compact synthesis across usable run-024 laps,
following the active plan's new whole-session condensation tranche.**
Preserve coverage, recurring signatures, counterexamples, uncertainty and provenance.
Quantified losses require comparable bounds and an explicit suitable reference;
neither the single best lap nor missing data may silently define the target.
Initial product budget to test: at most4,000 text tokens, six charts and24 images for
about20 min, with no mandatory video viewing. These provisional limits are not
measured model costs or proven sufficiency. No condensation implementation delivered yet.
The owner asked for one self-contained passage to submit personally. Prepared:
`run-028/reports/Passage_ACC_pour_analyse_IA.pdf` (17 pages, 19.2 MB), Les Combes,
HUD lap 6, source 334–352 s. Includes 1,081 samples as unsmoothed curves, neutral
transition times, missing-data list, 31 context views and 36 views at 0.1 s over
344–347.5 s (59 distinct native-resolution images embedded). Nine speed annotations
from run-026 reused; no new OCR. Source/image integrity and common-frame alignment
checked, PDF pages rendered/reviewed; no application-code changes or suite rerun.
Private pre-response reference: `run-028/interim/reference_avant_reponse.md`.
The user supplied an external response, preserved as `run-028/reports/reponse_externe.txt`.
Assessment: `run-028/reports/evaluation_reponse_externe.md`. Favorable reconstruction
on this one case: sequence, controls and off-track consequence are consistent. Visual
access is self-reported and supported by specific descriptions; model identity and
tool log unavailable. Its earlier right-side placement observation at 343–344 s was
confirmed against four existing frames and improves our initial reference. Cause
remains uncertain; its exercise changes several factors and cannot isolate placement.
The frozen reference remains untouched; separate errata correct two transcription
errors in that reference (the exported PDF/data were correct). No new OCR/code/test
campaign. The owner rejected adding video as the next step:17 pages for18 s is not a
scalable whole-session report. Clip supplement not produced and no longer scheduled
as the next action. Keep the existing PDF/response as a local perception experiment,
not a successful condensation or global-coaching test. Correct the representation
before expanding media. Detailed video remains optional source evidence.

M1's first-lap prototype and one user-mediated external reconstruction trial are complete;
full-session coverage and broader validation remain pending. For M2, obtain the ACC-on-Mac environment name
and usable duration, then prepare synchronized PC logging before consuming that window.
Do not start training or a paid service while those inputs are unknown.
