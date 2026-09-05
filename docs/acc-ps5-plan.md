---
summary: durable ACC PS5 telemetry roadmap, reliability stage gates, and blocked downstream coaching work
read_when:
  - working on ACC PS5 telemetry reliability
  - changing s, lap transitions, quality, segmentation, or coaching priorities
---

# ACC PS5 telemetry plan

Last verified: 2026-09-05

## Current state

The September 5 technical audit narrows the meaning of earlier validation claims:
representative internal-consistency metrics pass, but independent spatial accuracy
has not been established. The lap confirmer receives prefiltered/held observations,
and speed quality is lost in exported records. These integration defects must be
addressed before closing the remaining gates. See
`technical-audit-2026-09-05.md` for reproduced evidence and proposed next steps;
the proposed coaching/ML roadmap is not yet an approved implementation decision.

- capture_status: native_1080p60_validated
- controls_speed_gears_status: usable
- track_path_extraction_status: usable
- centerline_component_selection_status: temporal_persistence_and_unique_long_cycle_validated
- s_status: representative_clean_and_crash_gates_pass
- s_latest_validation_status: isolated_missing_boundary_dot_anchor_gap_resolved
- s_repair_design_status: generic_fusion_implemented
- long_capture_lap_transition_status: raw_observation_integration_defect_historical_replay_pending
- quality_propagation_status: speed_export_and_comparison_provenance_defects_other_fields_incomplete
- downstream_coaching_status: blocked

The repository provides a solid ACC PS5 video-extraction foundation, but it does not
yet provide trustworthy position-aligned coaching data. Reliability work is the only
active product direction until the three stage gates below pass.

## Validated baseline

The validated input is now a native 1920x1080, constant 60 FPS ACC PS5 recording with
the static full-map HUD and the explicit `ps5_full_map_1080p` profile. The extractor
can recover the map path, controls, speed, gears, lap observations, and red-dot
observations. This validates the capture and extraction inputs; it does not validate
the derived longitudinal coordinate.

On ten manually annotated frames from the clean 2026-09-02 BMW session, native 1080p
produced 10/10 exact matches for lap number, last-lap time, speed, and gear. The same
frames downscaled to 720p produced 9/10 lap-number matches, 0/10 last-lap-time matches,
and 10/10 speed and gear matches. Native 1080p60 is therefore the capture baseline for
future sessions. The 720p profile remains supported for historical recordings.

The result required calibrated regions and thresholded 3x lap-number preprocessing;
file resolution alone did not fix OCR.

`s` is intended to represent normalized progress along the extracted minimap path,
from `0.0` at a confirmed lap start to `1.0` near the next confirmed crossing. Legacy
CSV output exposes the corresponding value as `track_position` from 0 to 100. It is
an estimated path coordinate, not physical distance in meters.

## Failed `s` validation

The controlled Spa session requested by the previous plan was executed on
2026-09-01. It disproved the assumption that the existing `s` signal was ready for
segmentation.

Verified evidence:

- `s` first reaches at least 99.9% at 88.033333 seconds in a 180-second capture;
- `s` remains at or above 99.9% for 50.027742% of frames;
- the actual lap transition occurs around 178.2 seconds;
- after that transition, the reset produces plausible progress near zero;
- the longer session records `initial_s_anchor: fail_reproduced`.

The 2026-09-02 native 1080p diagnostic confirms three upstream root causes:

1. geometric start detection selects `(359, 0)` at path index `1141`, while confirmed
   crossings occur around `(70, 155)`;
2. the extracted path is an outline with parallel branches, so adjacent dot pixels
   can jump between path indexes such as `1905` and `370`;
3. red-dot detection selects the largest red contour before validating it, so a large
   red cockpit/background region can hide a valid 160–195 px² car dot.

On the 139,561-row clean-session trace, only 32 frames were directly accepted as
observed position. There were 63,282 missing-held, 40,254 backward-held, 18,323
forced-completion, and 1,196 jump-clamped decisions. The geometric-anchor lap first
reached 99.9% at 52.3167 seconds and remained there for 229.75 seconds before the real
transition.

The monotonic validator and forced-completion behavior amplify these upstream errors;
threshold tuning is not the root fix. The production correction must address dot
candidate selection, unique or continuity-aware path projection, and trusted lap
anchoring before reevaluating smoothing.

## Validated generic `s` replacement

The replacement is implemented on `feature/generic-s-fusion`. Production CLI and web
processing now use two-pass generic fusion; the legacy contour tracker is constructed
only by the explicit legacy diagnostic.

Representative clean validation covers two complete laps and three confirmed
boundaries. It records zero unconfirmed resets, zero nonlocal jumps, zero premature
completion-band entries, and a maximum `s_fused` spread of 0.001522 across 99 exact
odometric checkpoints, passing the 0.002 target.

Representative robustness validation covers two regular laps followed by one degraded
177.85-second lap. The degraded lap is rejected as a duration outlier and cannot change
the 6960.709 m effective calibration. Degradation remains visible through a 0.016398
checkpoint spread and 43.1 seconds of unavailable output; it is not hidden as observed
or held progress.

A new 2026-09-03 BMW session shows that this validation does not yet generalize to
every native 1080p recording. Lap confirmation succeeds from lap 0 through lap 4 and
three complete laps calibrate to 6962.810 m, but stable-map preparation rejects the
visual topology as `multiple_cycles`. Consequently 791.133 of 793.167 seconds are
unavailable. This safe failure reopens the visual-centerline portion of the `s` gate;
the cause must be diagnosed generically before downstream segmentation begins.

The cause is confirmed in the stable white mask. The broad ROI includes the left
mirror below the minimap. In the failing session, its persistent bright sky and border
form a 3,093-pixel component, larger than the actual 2,763-pixel map component. The
current area-dominance rule rejects the set as `multiple_cycles` before evaluating the
map itself. In the passing control, the map was only narrowly larger than all remaining
components combined. Component selection must therefore use unique circuit topology,
not largest-area dominance or a car-specific ROI crop.

The generic correction retains pixels present in at least 60% of sampled frames and
evaluates each disconnected component independently. It accepts exactly one cycle
longer than the configured ROI-relative minimum. The new BMW session and both prior
1080p controls now extract a centerline without changing the ROI or encoding a circuit
shape.

The generic boundary-anchor correction resolves the next independent limitation. On
the new replay, all four confirmed boundaries now use exact visual anchors and three
complete laps retain the same 6962.810185 m calibration. The first complete lap after
286.366667 seconds contains 8,515 fused rows instead of remaining unavailable. The
clean control retains its 0.001547 spread target, while the crash-heavy control still
rejects lap 6 for `duration_outlier` and keeps degradation explicit. All three captures
record zero unconfirmed resets, nonlocal jumps, and premature completions. The new BMW
spread increased from 0.003187 to 0.005740; this gate had no BMW spread threshold, so
that comparison remains recorded for later cross-session evaluation.

## Approved generic `s` architecture

The replacement must work across static full-map circuits; Spa is only the first
validation dataset. The approved design is documented in
`docs/superpowers/specs/2026-09-03-generic-s-fusion-design.md`.

It exposes three independently inspectable coordinates:

- `s_odometry`: progress from integrated `v * delta_t`, normalized using measured
  complete-lap distance;
- `s_visual`: absolute candidates projected onto a unique map centerline;
- `s_fused`: odometry-constrained visual progress with source, uncertainty, and
  reasons.

Official circuit length is an optional sanity check, not the primary denominator.
Actual driven distance changes with racing line, pits, and off-track travel.

Odometry is both a useful independent baseline and the temporal prediction used to
reject visually close but topologically impossible candidates. Visual observations
correct odometric drift. During missing visual evidence, short predictions remain
explicitly estimated and long uncertain gaps become unavailable.

Only a confirmed lap boundary may anchor or reset `s_fused`. No Spa-specific map,
corner coordinate, or track template belongs in the first implementation.

## Failed long-capture lap transitions

The longer 2026-09-01 Spa session records false lap transitions from lap-number OCR.
A false accepted transition resets the position tracker and can invalidate every
downstream `s` value for that lap.

Raw OCR observations must therefore be separated from confirmed lap state. A lap
transition requires stable, plausible evidence before it may update the lap or reset
the position anchor.

Lap-time OCR is also missing in the recorded sessions. It remains a known limitation,
but it is not the first blocker for position-aligned coaching because timestamps and
confirmed transitions can support the initial reliability work.

## Incomplete quality propagation

The domain `TelemetrySample` models field-level observed, missing, held,
interpolated, and anomalous states. Normalization can also retain source values and
anomaly reasons.

The active `TelemetryPipeline` now exports fused progress source, uncertainty, and
reasons, and speed distinguishes observed, held, missing, and anomalous evidence.
Lap number, gear, controls, and every analysis/API consumer still need the same
end-to-end treatment. Holding a value must never make it indistinguishable from a
fresh observation.

## Reliability stage gates

### Priority 1 — trustworthy `s` anchor and progression

Status: internal-consistency checks passed on the new BMW plus clean and crash-heavy
representative 1080p replays; independent physical-checkpoint accuracy is still
unverified, and the upstream lap-observation integration needs correction.
The isolated missing-boundary-dot failure is resolved without giving visual evidence
authority to create or reset a lap.

Required work:

1. build and validate `s_odometry` from speed and timestamps as an independent
   generic baseline;
2. select plausible red-dot contours using track and temporal context instead of
   rejecting the frame because the largest red region is invalid;
3. derive a unique centerline and continuity-aware projection so nearby pixels do
   not jump between distant contour indexes;
4. fuse visual candidates with odometric prediction and explicit uncertainty;
5. anchor `s_fused` from a trusted confirmed crossing rather than the false geometric
   point;
6. connect observed, predicted, interpolated, and fused quality to the domain boundary;
7. replay the clean and crash-heavy Spa sessions;
8. reevaluate completion and smoothing only after upstream observations are stable.

Exit criteria:

- `s` does not enter the completion band before the real start/finish crossing;
- `s` restarts near zero only at a confirmed new lap;
- forward progress remains coherent without hiding long invalid plateaus;
- known Spa passages map to stable `s` ranges across repeated laps;
- missing, held, or low-confidence position is explicit.

### Priority 2 — robust lap transitions

Status: pure confirmation state machine implemented, but production inputs are
prefiltered and held rather than raw OCR. Correct this integration before interpreting
the historical 2026-09-01 end-to-end replay as validation of fresh-observation consensus.

Required work:

1. retain raw lap-number observations separately from confirmed lap state;
2. require temporal consensus and a plausible increment;
3. prevent missing, stale, or isolated OCR values from resetting position;
4. replay the long 2026-09-01 session.

Exit criteria:

- an isolated OCR change produces no transition;
- one real increment produces exactly one transition;
- invalid observations retain the last confirmed lap with degraded quality;
- the long capture produces no false position reset;
- existing short-video and adapter behavior remains covered.

### Priority 3 — end-to-end quality propagation

Status: progress provenance reaches records; speed provenance reaches fusion but is
lost in records. The typed comparison API also strips modern progress fields. Lap
number, gear, controls, and analysis consumers remain incomplete.

Required work:

1. connect extraction observations to normalization and the domain contract;
2. provide typed, field-level quality at the analysis boundary;
3. preserve anomaly reasons in a machine-readable output;
4. keep legacy CSV/API compatibility through an explicit adapter or versioned
   extension.

Exit criteria:

- analysis receives normalized telemetry rather than unexplained legacy dictionaries;
- `s`, lap number, speed, and controls carry independent quality states;
- held values remain distinguishable from observed values;
- anomaly reasons reach the output consumed by analysis;
- existing consumers have tested compatibility behavior.

## Imperfect passages / passages imparfaits

Imperfect evidence must never disappear silently. Occlusion, missed red-dot detection,
OCR jumps, uncertain transitions, held values, and interpolation remain visible in
quality metadata. This is the durable contract for qualité and anomalies: analysis
may exclude a low-confidence zone, but raw observations remain available for human
validation and extractor improvement.

## Blocked downstream work

The following work is blocked until all three reliability gates pass on controlled
Spa evidence:

- corner segmentation;
- driving-event extraction;
- lap-to-lap and external-reference comparison by `s`;
- explainable coaching rules and skill scores;
- coaching dashboards and generative feedback;
- lateral coordinate `d`.

The first milestone after the gates pass is one manually reviewed Spa corner segment,
not a complete catalogue of the circuit.

## Future lateral coordinate `d`

`d` will represent signed lateral distance from a reference line. It is not calculated
today because the video minimap does not yet provide validated track width or lateral
projection. Future work must define reference geometry, sign, unit, confidence, and
evaluation on known corners.

## Next planning gate

Generic boundary visual-anchor recovery now passes the new BMW plus both representative
controls. The next reliability work is the historical 2026-09-01 long-capture replay
through the new lap confirmer, followed by remaining field-quality propagation and
explicit CSV/API compatibility. Corner analysis remains blocked until those gates
pass; the next product-facing milestone is still one manually reviewed corner.
