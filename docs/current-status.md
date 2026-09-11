---
summary: living A9 handoff for delivered admission corrections, final development replay and remaining coverage evidence
read_when:
  - starting any task
  - resuming reliability corrections or changing stage-gate status
---

# Current status

Last verified: **2026-09-11**. Branch `codex/coaching-reliability`; A6 checkpoint
`f060637`, A7 validator introduced by `006629f`. Recent Git history owns later IDs.
Default delegation stays below GPT-6 Astra with explicit model selection. The owner
authorized one bounded Astra visual trial on 11 September; see `astra-review-trial.md`. Push is authorized; no merge to main. The user
explicitly requests autonomous visual verification wherever reliable, with uncertainty
preserved; do not ask them to repeat accepted or reliably agent-verifiable reviews.

**A0–A7 implementation/evaluation complete. Gate A FAILS; B blocked. C remains
separate/inactive.** A8 changes modern speed extraction; acceptance targets remain
unchanged. Full BMW/crash development replays and scoped measurements are published.

Active correction specification: `signal-treatment.md`.
Active plan: `plans/2026-09-09-admission-corrections.md` (**C1/C2/C3 delivered; fixed-ROI counter reviews complete; complete-system demonstration next; independent acceptance open**).
Previous A8: `plans/2026-09-09-fresh-measurements.md` (completed within available evidence).
Parent product specification: `specs/2026-09-05-reference-corner-coach-design.md`.
Completed A7 execution: `plans/2026-09-05-coaching-reliability.md`; Gate A still fails.
Contract: `capture-validation.md`. Full results: `capture-validation-results.md`.
Preserved semantic constraints: `coaching-reliability-resume.md`.

## Immediate owner priority — complete-system demonstration

The owner explicitly redirects effort from exhaustive annotation to a real end-to-end
trial. Follow `real-system-trial.md` before further evidence campaigns. Reuse completed
counter truth. Process the existing incidents video through the actual shared pipeline,
**open and show its output**, and compare a few useful braking/acceleration/incident/lap
windows with the source. Report gaps and unavailable progress rather than delaying the
trial for complete visibility annotations. Fix only demonstrated material defects.
No new exhaustive review, reviewer qualification, agents or threshold search is needed.

Gate A remains FAIL and coaching B/R stays blocked; this does not block a development
trial and visualization of current outputs. No new recording is required for this step.
Independent testing on a distinct reserved capture comes later. Respect the user's quota.

## Incidents counter review completed — run-022

Primary review covers all **24,267 distinct incidents numeric-ROI states**, mapped by
exact raw RGB equality to **29,402 source frames**. Every state is readable. All source
ROI mappings, sheet tiles, source identity and counter-path compatibility rechecked.
No rejected reviewer labels, OCR rerun, code/configuration or threshold change.

**29,402/29,402 counter observations exact;4/4 events, zero missed/extra events.**
Scoped P95 midpoint error8.3ms, confirmation66.7ms. The complete numeric sequence has
only3→4,4→5,5→6,6→7. L2's timer-reset10→11 remains distinct from counter14→15.
This is unique-state review plus exact mapping, not manual inspection of every duplicate.

The result uses the **isolated counter path**, whose `last_observed_time_s` is null;
it is not full-source telemetry-v2 freshness/parity or independent acceptance.
**Gate A FAIL; B/R blocked.** Full pipeline verification and speed/independent blockers
remain. Details: `incidents-counter-results.md`; ignored `run-022/START_HERE.md`,
`reports/crash-results.json`, `result-audit.json` and `final-integrity.json`.

## BMW counter review completed — run-021

Owner resumed. Primary review now covers all **4,159 distinct BMW numeric-ROI states**,
with exact RGB mapping to **47,589 native source frames**. Every decoded source ROI was
rechecked against its representative; sheet/source/payload hashes and current extraction
compatibility pass. This is unique-state review plus exact mapping, not manual inspection
of every original sheet. Rejected agent labels remain diagnostic only.

**47,589/47,589 fresh counter observations are exact.** All four numeric transitions are
found with zero missed/extra events; scoped precision/recall1.0, P95 midpoint error8.3ms,
confirmation delay66.7ms. No additional numeric reset/change appears in the ordered ROI
sequence. The initial3840-frame QA lot agrees21/21. BMW fixed-ROI event check passes;
**overall Gate A still FAILS; B/R blocked**. No code/configuration/threshold changed.

This is one development recording, not independent acceptance or physical crossing truth.
Incidents counter review is now completed above; speed/independent blockers remain. Details and evidence:
`exact-counter-state-review.md`, ignored `run-021/START_HERE.md`,
`reports/bmw-results.json`, `result-audit.json` and `integrity.json`.

## Previous bounded trial — run-019

The owner authorized the bounded Astra experiment. One gpt-6-astra sub-agent with high
reasoning inspected 14 sheets and 11 native crops. **All 1,355 presentations agree with
root's withheld pixel references (1,348 distinct source frames); all 8 transition
brackets match and all 11 disputed crops are read correctly.** No false absence or
uncertainty was reported on this fixed lot. Source/media/code/config integrity passes.

This qualifies only the small trial. Prior short Sol qualification also passed before
sustained failure; no general reliability, real-HUD-absence detection, other-circuit
performance or full 803-sheet coverage is implied. No new recording or OCR replay.
**Gate A FAIL; exhaustive recall not_evaluated; B/R blocked.** Old failed labels remain
rejected and preserved. No job remains active.

Results: `astra-review-trial.md`, ignored `run-019/reports/trial-results.json` and
`run-019/reports/final-verification.json`. The model exception is recorded for this
bounded visual trial; it is not blanket authorization for unrelated Astra delegation.

## Previous recovery work — run-018, 11 September 2026

Owner resumed after the shutdown checkpoint. No job now remains active.
**Exhaustive visual annotation remains blocked by reviewer reliability.** The single
identified original-detail image protocol passed960/960 pilot cells, but sustained
passes again produced false absences (BMW453 visibly0; incidents799 visibly4). A compact
presentation was not qualified either. Failed ledgers are diagnostic, never truth.
Do not count them as reviewed coverage or resume from their last sheet numbers.

Root independently checked all **eight published counter-event predictions** in their
pixel windows:4/4 BMW and4/4 incidents match, P95 about8.3ms. This is a targeted,
output/known-window-selected check; **recall and the lap-event gate remain
not_evaluated**, because additional missed events cannot be ruled out. L2's original
timer-reset approval stays separate from the actual numeric-counter update.

Technical reuse remains verified: current-code full BMW artifact in run-015 and fresh
incidents counter-only extraction from run-017. No OCR rerun, code/config/threshold
change, old annotation rewrite or holdout work. **Gate A FAIL; B/R blocked.**

Evidence and limits: `counter-review-recovery.md`, ignored `run-018/START_HERE.md`,
`reports/method-outcome.json`, `reports/targeted-event-results.json` and
`reports/reuse-integrity.json` under run-018. Run-017 and run-018 exploratory annotations
remain rejected/preserved. The subsequent explicitly authorized bounded Astra
experiment is documented above; these older failed labels remain unaccepted.

## Prepared dossier — run-016

The exhaustive native1080p counter dossier is **prepared, not fully visually reviewed**:
47,589 BMW + 29,402 incidents frames, **76,991 ordered cells on 803 sheets**,
132 scene contexts. Source/metadata/cadence and all sheet/crop/index hashes and pixel
correspondence pass. Every frame retains its own row/cell; identical crop pixels share
storage only. All preparation labels remain unreviewed/null/unknown. No new OCR,
telemetry replay, code/configuration or acceptance target change occurred.

Original three user boundary intervals and two run-015 agent reviews remain separate
and preserved. A targeted root review of incidents frames8–19 confirms timer reset
at10→11, numeric counter3→4 at14→15. The old L2 interval coincides with timer reset;
do not silently reuse it as counter-event truth or change its approval.

Entry: `lap-counter-dossier.md`, ignored `run-016/START_HERE.md` and
`run-016/reports/lap-counter-review-dossier.json`. **Gate A FAIL; B blocked.**
Exhaustive counter semantics and independent acceptance remain open; no user video
or clarification is needed for the next review. No job remains active.

## Previous calibration tranche — run-015

The first complete BMW calibration-lap dossier is reviewed exhaustively: **8,729
readable images**, including padding, on 182 sequential sheets plus all 40 scene
contexts. Two gpt-5.6-sol reviewers own disjoint halves; root independently reviewed
the two counter boundaries. No user approval is implied. Source metadata/cadence,
every sheet cell and all media hashes pass. No code/configuration changed.

A frozen full-source production replay exports **47,589 frames**, exact frame/time
alignment. The calibration interval (17172–25876) has **8,679/8,705 fresh speed
observations (99.70%)**, 26 explicit abstentions. One lap is now accepted, effective
integrated length 6,950.81 m, an internal estimate rather than metric accuracy.
Internal odometry bridges short gaps (45 interpolated edges); published speed stays
null. The reported zero missing odometry fraction is not 100% raw speed coverage.

`s` becomes available on **8,473/8,705 lap frames**, with 232 uncertainty rejections.
Only 1/2 BMW landmark passages is now measurable; dispersion remains not_evaluated.
19/19 approved speed points remain exact; all 564 fixed BMW segment frames are
admitted. Across the entire source, raw speed OCR and both pedal observations are
unchanged versus run-011. Current results: `calibration-lap-results.md` and ignored
`run-015/reports/results.json`; production artifacts: `run-015/processed/bmw-session/`.

**Gate A FAIL; B blocked.** Exhaustive native1080p event truth, broader numerical
accuracy and distinct independent validation are still missing. Incidents segment
V-CRASH-15 remains below 95% in run-014. Full-source BMW visibility still has 38,679
unknown frames. One calibrated development lap does not validate all laps or spatial
precision. No further source/video is required for the next development task; a new
recording will be required for independent acceptance. No job remains active.

## Previous verified tranche — run-014

The 32 fixed development segments / 1,247 individual images and all 64 scene
contexts are reviewed: BMW 564 visible, incidents 683 visible, zero absent or unknown
inside the scope. Root (gpt-6-astra) and gpt-5.6-sol retain separate authorship;
no user approval is implied. Media/source hashes and native 1080p60 cadence pass.

Fresh selected-source speed reader → admission → normalization gives **564/564 BMW
and 679/683 incidents**, versus frozen sparse-review 39/564 and 40/683. The 40
preserved approved numeric points are exact (MAE/P95 0/0). Other frame accuracy is
not established by visibility. Four incidents abstentions retain raw OCR/reasons;
one rejects a correct 39 after a real displayed 66→39 drop. No policy tuning.
**V-CRASH-15 remains below target: 28/31 = 90.32%. Gate A FAIL; B blocked.**

This is scoped speed-path evidence, not a full pipeline/artifact replay or a new
gate pass. Calibration and `s` remain unavailable; complete-lap visibility,
exhaustive 1080p lap events and a distinct reserved independent recording are missing.
Full traceability and exact paths: `speed-visibility-results.md`, ignored
`run-014/reports/scoped-results.json`. New reviews are standalone; old annotations,
approvals and runs are preserved. One floating end-bound export error was detected
and corrected in a separate incidents canonical derivative; no code/config changed.
No job remains active after publication. No user image clarification is needed.

## Current implementation

**Latest owner constraint: native 1920×1080, exactly 60 fps CFR only.** Other videos
are rejected from metadata/cadence checks before frames/OCR, including 720p and
59.94 fps. CLI and web default to the 1080p profile. No more 720p extraction or
investigation; preserved historical results do not qualify the active 1080p gate.
An exhaustive 1080p event review is still needed. Format RED/GREEN evidence is in
run-012/reports; 317 tests pass. This code change invalidates previous extraction fingerprints.

A9 C1 now requires source-bound speed visibility in the modern pipeline; unknown
or absent HUD abstains while raw OCR survives. See `speed-visibility.md`.
New outputs are under run-011; 207 prior evidence files verified before editing.
New code invalidates run-010 acceptance compatibility; its measurements stay frozen.
Focused RED/GREEN and source binding tests pass; 303 full-suite tests pass for C1.
C3 foreground-bound modern lap OCR now passes all ten approved endpoints (old 5/10),
with 307 full-suite tests. Full historical replay now detects all five approved
events without extras (P95 0.0083335 s). C2 rejects a
global word-mode speed switch: on 86 unique reviewed frames it introduces errors.
C2 now uses predeclared causal rate admission: 100 m/s², at most 0.25 s within a
reviewed context, explicit null on rejection and fresh recovery. Cached development
evaluation has 83 exact/3 abstained/0 admitted wrong out of 86. Final actual replay
confirms those results on 133,237 total source frames; 314 full-suite tests pass.
Sparse speed review does not establish whole-lap coverage or calibration.
High-impact rates above the policy can abstain.
The first full replay exposed a BMW lap regression from global foreground cropping.
Cropping is now enabled only on the historical 720p profile; 1080p retains its
previous ROI. Final `-v2` replays restore BMW 2/2 and crash 1/1 approved event matches,
and preserve historical 5/5 without extras. Earlier attempts remain diagnostic.
Current A9 evidence and limitations: `admission-correction-results.md`.

**Frozen A9 gate, before the 1080p-only decision:** `run-011/reports/gate-a-final.json` FAIL. Software, lap-event and
timebase checks pass; speed coverage fails (39/564 BMW, 40/683 crash). Overall field
accuracy and independent holdout remain `not_evaluated`. No calibration lap is
admitted and `s` is unavailable (0/4 development landmark estimates). Exact approved
speed points remain 40/40; continuous speed visibility is still unreviewed elsewhere.
Fingerprint: `44b5226547fce8a99659fb8b55c5539933aa8ed4cc76b4478d5575a1e60adac7`.
No artifact job remains active.

## Approved delivery priority and session handoff

The owner approved this order on 2026-09-09: finish A in native 1080p60, then deliver
one useful B dossier on a Spa corner with an explained compatible reference,
mandatory paired trajectory images, one exercise and follow-up (B9/B10). Metric
`d` is outside B and must not become its prerequisite. Reconsider the separate
replay research plan C only if limitations of the first visual debriefs justify it.
The specification's coaching validation « gate C » is not that research plan.

Case/reference preparation may run alongside A; implementation B stays blocked.
The user can prepare a 1080p60 reference and a separate fresh validation recording,
kept uninspected until reservation under frozen code. Existing pilot captures remain
the starting point; a second circuit follows the first useful case. See
`coaching-implementation-roadmap.md` for roles and required sources.

The 10 September request explicitly resumed the work after the prior documentation
session. The authorized short-segment review and measurement are now complete;
this does not authorize downstream B/C implementation. Run-013 remains frozen
verification of the 9 September decision.

Real extraction/pipeline RED tests reproduced 246→255, 179→188 and held invalids.
Modern speed now publishes strict fresh OCR values or explicit absence, retaining
raw text and reasons. Legacy median/holding stays isolated in `extract_speed`.
A8 added no temporal speed heuristic; A9 C2 adds admission only. No pedal smoothing
or regression R was added. S3 found
a separate CSV/API timestamp precision defect, fixed with round-trip float parsing.
Real decoder/artifact/API tests protect pedal dynamics, nulls, old HELD and odometry
provenance; no consumer substitutes an estimated speed for the measured field.
Frozen A8 evidence: `fresh-measurement-results.md`, ignored run-010. A9 replaces
the unguarded HUD contract and fixes the reviewed historical event failure;
coverage and independent acceptance still block B and R.
An A8 review of six output-selected development frames confirmed two wrong
OBSERVED speeds (162→4, 177→7). C2 now rejects these; broader numerical admission
still needs compatible full-source and independent validation.

A8 run-010 full replays cover 47,589 BMW + 29,402 crash frames. Speed is exact on 40/40
approved development points (MAE/P95 0/0); fixed-segment speed availability is
564/564 and 681/683. Raw OCR and pedal observations are unchanged on all frames.
Separate 44-frame agent image review has 43 exact fresh readings and one explicit
out-of-range abstention. These windows overlap four approved points.

Run-010 gate `reports/gate-a-final.json` remains **fail**: software, scoped coverage and
development timebase pass; HUD contract and extra speed readings fail; full new-code historical event
recall and independent holdout remain `not_evaluated`. New fingerprint:
`7120555640e848989484cd9f681bf10748d13cecb2cdc8c4241e5e9e677fe48a`.
Calibration and `s` were replayed; BMW loses two available `s` frames, and all
changes/denominators are recorded in `fresh-measurement-results.md`.

Original development diagnosis: **40/40 raw OCR speed readings are exact** on
the selected 19 BMW + 21 crash labels. Subsequent median-filtered outputs include
246→255 and 179→188. Scope is these points only, not all frames. Read-only proof with
input hashes: `data/lab/coaching-reliability/run-009/reports/speed-raw-vs-output.json`.
The benefit of a regression curve remains a hypothesis; no model was tested or added.

## Stable implementation baseline

Generic progress implementation and representative validation complete; technical
ACC Tasks 1-10 complete. Those historical internal-consistency checks do not validate
independent Gate A. Design: `docs/specs/2026-09-03-generic-s-fusion-design.md`.
Boundary-anchor plan: `docs/plans/2026-09-05-generic-boundary-visual-anchor.md`.
Earlier milestone record — Last completed implementation plan: `docs/plans/2026-09-04-temporal-centerline-selection.md`.

## Frozen A7 authority (old fingerprint only)

All run paths below are relative to ignored `data/lab/coaching-reliability/`.
A6 remains accepted and unchanged: `run-007/processed/accepted-corpus-v4/index.json`,
proof `run-007/reports/a6-acceptance.json`. Original labels, approvals, six physical
intervals, recording IDs, roles and holdout reservation remain intact.

**Frozen final A7 gate:** `run-008/reports/evaluation-final-v2/gate-a.json`.
These results are not transferred to the changed A8 extraction fingerprint.
Human-readable report: `run-008/reports/RESULTS_A7.html`.
Earlier `run-008/reports/gate-a.json`, `evaluation-v2/` and `evaluation-final/`
are superseded diagnostic snapshots. Do not use their old pending statuses or
unqualified release offsets as final acceptance results.

| Gate check | Final result |
| --- | --- |
| software_regressions | pass: 24 capture + 9 diagnostic; 288 full-suite tests |
| lap_events | fail: 0/5 approved historical counter increments detected |
| field_accuracy | fail: speed exceeds targets; holdout has 6 fresh readings on 20 absent-HUD labels |
| field_coverage | pass, only 109 fixed short segments / 5,463 frames / 91.05 s |
| timebase | pass, all five full source artifacts and independent capture checks |
| holdout | fail; original extractor/settings reservation remains compatible |

Speed MAE/P95 km/h: BMW **2.315789/9** (19/19 fresh labels), crash **1.7/6**
(20/21), holdout **1.551724/5.15** (58/60). Brake and throttle MAEs pass 5 points,
with 100/100 readings per field. Scoped speed availability is 100%, 96.1933%,
99.0275%; each pedal is 100% on those segments. This is not whole-lap coverage.

Landmark circular `s` ranges: BMW 0.000120233 (2/2), crash 0.001578158 (2/2),
holdout unavailable (0/2, unanchored). No conversion to meters is justified.

## Reviews, exclusions and provenance

- User approval covers only H01–H05: `run-008/reports/user-historical-approval.json`.
  Agent's separate all-frame counter review confirms exhaustiveness and rejects
  four old suspect increments: `agent-historical-review.json` in the same directory.
- Independent agent visibility review uses first/last and temporal min/max sheets
  incorporating all 5,463 target images: `agent-visibility-review.json`. It is
  qualitative, not a calibrated probability; extrema do not preserve frame order.
  Point approvals were not expanded by implication. Reviewer identity is preserved.
- Current derived labels: `run-008/processed/agent-reviewed-corpus-v2/` and
  `historical-approved-v2/`. Reviewed artifacts: `{bmw,crash,holdout}-reviewed-session/`;
  historical and additional clean artifacts: `{historical,clean}-session/`.
- Final pedal timing: 16 onset/reapplication markers in 15 windows, all on holdout;
  12/12 brake onsets (P95 0.0475 s), 4/4 reapplications (P95 0.00833345 s).
  Two extra nearby crossings are unannotated candidates, not proven false positives.
- E16 remains full throttle at **30397**, approximate initial 60% context only.
  E16, two first-visible-brake markers and seven generic release starts are excluded
  from the 5% latency metric. Release-start images show filled bars; falling release
  latency remains `not_evaluated`. Proof: `pedal-semantics-review.json`. No original
  event was relabelled; these are not B4 detector results. Blips and E17 causality
  retain their original restrictions.

Gate SHA-256: `8b0d323bef702ce8e7dafa4e68c2be2c736f7c06b55d221c4a5ea8f8f6551373`.
Measurement fingerprint: `d9808e44a6abfb24b78e33d14879409b61c7e727fbeaf6bb15dac67afaa50ae3`.
`evaluation-final-v2/integrity.json` and `input-integrity.json` verify preserved A6
and unchanged reserved extraction settings/modules. Three A7 metric-definition
settings were fixed before results; all old acceptance targets remain unchanged.

## Verification and exact next action

288 full-suite tests pass, including the 24 focused capture and 9 diagnostic tests;
RED logs, final tests, docs discovery and local reproduction/review scripts remain
under `run-008/`. Private/generated evidence is ignored. The final validator reads
telemetry-v2 without OCR. The final correction also prevents generic release starts
and sparse extra crossings from being misreported as latency errors/false positives.

Run-010 preserves S1 RED (5 tests, 6 functional failures), S2 GREEN (5 tests),
16 OCR/legacy tests, 91 S3 focused tests and a 298-test passing full suite.
`reports/preservation-before.json` and `preservation-after.json` verified 128 prior
files and source sizes/hashes before/after edits. The old gate/reservation and A6
authorship remain unchanged. Final 24 capture/298 full tests are in
`reports/final-focused.txt` and `final-full.txt`.
Known holdout run-008 cannot become independent again or receive a rewritten reservation.

Final run-011 logs: `reports/final-focused-v2.txt` (103 tests), `final-full-v2.txt`
(314 tests), and `preserved-final-v2.json` (207 unchanged prior evidence files).

Run-014 final verification: focused speed/format/capture/layout tests and the full
suite, docs discovery, diff check and preservation hashes are recorded in
`reports/final-verification.json`; no code or acceptance setting changed.

Run-015 final verification: focused calibration/progress/admission/artifact tests,
317 full-suite tests, media/source preservation, docs discovery and diff check are
recorded in `run-015/reports/final-verification.json`.

Run-016 final verification: focused capture/format/lap/layout tests and the full
317-test suite, old evidence preservation, complete preparation integrity, docs
discovery and diff check are recorded in `run-016/reports/final-verification.json`.

Run-017 pause checks: focused and full tests, docs discovery and diff check are
recorded under `run-017/reports/`. No repository code/configuration changed.

Run-018 verification: focused/full tests, saved-source/payload integrity, docs discovery
and diff check are recorded under `run-018/reports/`.

Run-019 final verification includes preserved inputs/code/config, focused/full tests,
docs discovery and diff check; logs are under `run-019/reports/`.

Run-020 pause verification: focused/full tests, docs discovery and diff check are
recorded in `run-020/reports/`. No active job remains.

Run-021 verification: completed exact mapping and output audit; focused/full tests,
docs discovery and diff check recorded under `run-021/reports/`.

Run-022 verification: full exact-state media/mapping audit, complete counter evaluation,
prior BMW evidence preservation,45 focused tests and317 full tests; docs discovery and
diff check logged under `run-022/reports/`.

**Next action:** execute `real-system-trial.md`: run the complete incidents video through
the real shared pipeline with existing visibility evidence, open the generated report,
and inspect a small set of useful video-aligned windows. Reuse frozen counter truth;
show missing speed/progress honestly. Deliver the visible result before any further
exhaustive review. No new recording or Gate A pass is required to demonstrate it.
