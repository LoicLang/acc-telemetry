---
summary: run-032 timing review finds missed throttle transitions from HUD fragments; run-031 remains the data baseline
read_when:
  - starting repository work or choosing the exact next action
  - checking current extraction capabilities, evidence and platform boundaries
---

# Current status

Last verified: **2026-09-15**. Work branch: `codex/video-control-episodes`, created
from main at `6b2c04b`. Episodes delivered; native pedal ROI calibration now corrected.
No sub-agents, exhaustive review, threshold campaign or OCR replay. The duplicate
plan copy was removed after byte-for-byte comparison with the version in `6b2c04b`;
the plan linked below is the only active plan.

## Vision and priority

**Final product: a persistent driving-data platform that an AI agent can navigate.**
It will expose session summaries, trajectories, references, comparisons, recurrences
and evidence through tools/MCP, with optional skills for investigation. Human reports
are optional views. The agent analyses driving; our software supplies traceable facts.

**Current work: recover and qualify the useful data from video first.** The owner
explicitly deferred platform implementation and agent navigation until the data
foundation exists. Existing local artifacts are sufficient for the next increments.
PC video+telemetry may support spatial labels; future direct PC acquisition should
reuse the same normalized concepts. No MCP server, new database or navigation skill
is implemented or required for the next task.

Active plan: `plans/video-to-agent-platform.md`.
[Code audit](video-data-audit.md) maps all72 catalogue entries to actual code.
[Research catalogue](driving-metrics.md) defines the target and its input requirements.
[Architecture](architecture.md) describes the existing pipeline and future boundaries.

## What the code actually provides

- Native1080p60 CFR preflight, source frames/time, immutable-source artifacts.
- Fresh speed, brake/throttle percentages, gear, confirmed HUD lap number/events.
- Estimated normalized progress `s`/`s_fused` in0–1; `track_position` in percent.
- A HUD steering-dot candidate in−1…1, **not a calibrated physical steering angle**.
- Neutral pedal on/off and gear-change candidates; missing-data intervals and coverage.
- Diagnostic position alignment/delta, coarse per-lap summaries, manual-landmark
  time intervals, annotation-based accuracy/event metrics.

New: candidate brake/throttle episodes, temporal descriptors and frame-linked evidence
([contract and reproduction](control-episodes.md)).
Not delivered: generally qualified episodes, automatic physical corner landmarks,
metric `s_m/d_m`, trajectory/orientation, dynamics or recurring-loss analysis.
TC/ABS remain missing in modern extraction. `lap_time_s` is empty in run-024 despite
a legacy OCR method existing. Context/incident scene descriptions were manually supplied.
Detailed caveats and code links are in the audit.

**Gate A: FAIL; `coaching_eligible=false`.** Availability is not accuracy. Historical
run-024/029 full throttle reads about94 %. The corrected native profile reaches100 %
at reviewed full-scale points; small residues and impact-speed abstentions remain.
No smoothing or invented visibility. Hidden physical quantities require a justified
estimator/other source or remain unavailable; the72-entry catalogue is not a promise
that every channel can be reconstructed exactly from arbitrary video.

## Reusable evidence and actual outputs

All run paths below are relative to ignored `data/lab/coaching-reliability/`.

- run-024 `processed/crash-session/`: 29,402 samples, hashes/envelopes rechecked by
  `read_session_artifacts()` during the audit. Speed29,298; each pedal29,402;
  gear28,913; progress26,844; physical steering/TC/ABS unqualified.
- Source: `data/lab/2026-09-03-generic-s-fusion/crash-representative.mov`,453613415 bytes,
  SHA-256 `b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124`.
- run-021/run-022: finished BMW/incidents counter truth; reuse, no exhaustive reread.
- run-026 `reports/session_coaching.md`: three reviewed passages; retained/reproducible
  via [its implemented contract](specs/2026-09-13-session-coaching-report.md).
- run-027 `reports/lap-4/index.html`: actual full-lap viewer,14 manually routed zones,
  95 neutral candidates and frame-synchronized video. [Commands](perception-package.md).
  Local preview was started on8767; check availability before claiming it is running.
- run-028 `reports/Passage_ACC_pour_analyse_IA.pdf`:17 pages/18 s,59 distinct images.
  External response and evaluation are in `reports/reponse_externe.txt` and
  `evaluation_reponse_externe.md`; frozen reference in `interim/reference_avant_reponse.md`.
  Reconstruction locally favorable, not proof of scalable condensation or coaching.

The audit ran existing event functions across all run-024 samples:316 candidates
(44 brake on/off pairs of counts,46 throttle on/off counts each,135 gear changes and
one initial active-throttle state). Run-029 now pairs the 181 pedal candidates;
135 gear candidates are outside this increment.
Existing tests were read/reused; source videos were not decoded again for this audit.

## First episode increment — run-029

- `processed/control-episodes/`: structured JSON, original pedal samples, annotation
  comparisons and integrity manifest. 91 episodes (44 brake, 47 throttle); 89 bounded,
  two throttle fragments at session edges; 89 resumption relations, 61 candidate overlaps.
- No pedal gaps in this source. Every invalid/missing row or absent frame splits
  evidence in the implementation; missing boundaries produce null durations.
- Duration, observed peak/first peak time, last-maximum-to-off tail and mean HUD slope.
  True release onset, internal modulation classification and calibrated full throttle
  remain unavailable. No inherited speed/lap aggregates used or changed.
- `reports/examples.md`: three braking episodes and one throttle episode checked
  against existing sparse points/visibility. 21 points per pedal reproduce known biases.
  B2 onset 11246 falls in 11245–11246; throttle-off 11255 lags reported release by
  0.250–0.267 s. Definitions differ; no complete episode temporal accuracy demonstrated.
- 33 focused tests and four documentation tests pass; artifact hashes and all 29,402
  pedal rows preserved, 181 events
  unchanged, four example calculations checked. Source video never opened by this work.

## Pedal calibration correction — run-030

The native1080p pedal ROI included9 pixels beyond the144-pixel bar, yielding
144/153×100 =94.12 % at full scale. Both configured widths are now144; color/event
thresholds and historical profiles are unchanged. On21 existing annotated images:
brake MAE1.60→0.25 points, throttle3.12→0.41; all9 full-scale points read100 %.
24 focused tests pass after reproducing the defect. No OCR or full-video replay.
[Calibration details](signal-treatment.md); local point checks and verification in
`run-030/reports/`. Run-024/029 remain immutable historical outputs using the old
calibration; they have **not** been recalibrated by this configuration fix.

## Calibrated session and episodes — run-031

- `processed/crash-session/`:29,402 native frames; pedal-only refresh using144px ROI.
  All58,804 old-geometry pedal readings reproduced during decoding. Input size/hash,
  native format/CFR, decoder timestamps and full coverage verified; no OCR.
- Other samples/observations/CSV fields, original qualities/reasons and missing values
  verified unchanged. Parent run-024 and old run-029 outputs preserved. Mixed provenance
  is explicit in `manifest.pedal_refresh`; the old acquisition code belongs to inherited
  channels, the refresh code to pedals.
- `processed/control-episodes/`:91 episodes (89 bounded),181 events,89 resumption
  relations,61 intersections, no pedal gaps.177 events retain their exact timing.
  Brake-off1464→1451 and throttle-off2621→2624; throttle off/on12982/13018 disappears,
  on/off20190/20305 appears. Same counts do not imply the same episodes.
- Four example episodes retain their durations but reach100 % peaks. The first/last
  exact peak can move because the full-scale plateau is now represented at100 %.
- `reports/results.md` and `comparison.json`: point MAE brake0.254/throttle0.407;
  all9 full-scale annotations read100 %. B2 onset and release comparisons unchanged;
  continuous timing and the newly appearing events are not independently validated.
- 31 distinct focused tests pass (replacement, missing evidence, decode failure cleanup,
  episode and artifact checks). No video replay after successful publication.
  [Refresh command and provenance](session-artifacts.md).

## Targeted temporal review — run-032

- 208 native frames in8 windows reviewed:67 reused,141 newly decoded after format/source
  checks. No OCR, full replay, threshold change or source mutation. New visual labels
  are provisional non-blind model review, not independent/human-approved ground truth.
- B2 brake onset agrees with existing human11245–11246; model-reviewed end11422–11423
  gives a local boundary-duration interval2.933–2.967s containing the computed2.950s.
  This does not qualify the entire interior or physical input latency.
- Throttle disappearance2620–2621 vs candidate2624:50–66.7ms offset. Disappearance
  20302–20303 vs candidate20305:33.3–50ms. Different definitions/review status remain
  separate; no global MAE or general precision assertion.
- Visible off/on12982/13018 is missing from the calibrated event index. Mask fragments
  under HUD text create3/144=2.0833%, keeping the hysteresis state active. At20196,
  sparse upper-row/text pixels produce5% despite an apparently empty bar body and
  support confirmation of an episode whose continuity is not visually supported.
- `extract_bar_percentage` chooses the longest fragment anywhere, despite its comment
  describing left-origin fill, and excludes empty rows from its percentile. This is
  a concrete extraction limitation; no detector changes were made during this review.
- `reports/timing-review.json`: capability-specific observations, frame brackets,
  candidate/confirmation offsets, nulls for missing/ambiguous references. `results.md`
  links all8 native sheets. First/last maximum and changed brake-off remain partly
  ambiguous; no physical release onset inferred. Data baseline remains run-031.

## Demonstrated issues to account for in the next increment

- Do not treat normalized `s` as metres or minimap centerline as actual trajectory.
- `generate_summary()` counts five HUD numbers where only three laps have both bounds.
- Its all-missing speed aggregate still returns0.0; reproduced in memory. Correct it
  before reusing that aggregate, preserving nulls and field quality.
- Coarse statistics do not distinguish clean/partial/incident laps or qualify phases.

## Exact next action

**Correct the pedal extractor's admission of disconnected HUD text/graphic pixels,
starting with the run-032 counterexamples.** Preserve genuine low fill and full scale;
do not raise off thresholds to hide residuals. Verify the bounded windows and existing
calibration points, then recalculate affected episodes. No platform or trajectory
implementation before resolving this demonstrated control-data issue.

For subsequent spatial work, ACC-on-Mac software/service and usable duration are still
unknown. Prepare collection before consuming a limited PC window. Dataset/model work
must demonstrate synchronization, geometry and transfer; none has been launched.
