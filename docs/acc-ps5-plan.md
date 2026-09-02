---
summary: durable ACC PS5 telemetry roadmap, reliability stage gates, and blocked downstream coaching work
read_when:
  - working on ACC PS5 telemetry reliability
  - changing s, lap transitions, quality, segmentation, or coaching priorities
---

# ACC PS5 telemetry plan

Last verified: 2026-09-02

## Current state

- capture_status: native_1080p60_validated
- controls_speed_gears_status: usable
- track_path_extraction_status: usable
- s_status: failed_validation
- long_capture_lap_transition_status: failed_validation
- quality_propagation_status: incomplete
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

The current code path can amplify a bad initial anchor: path extraction installs a
geometrically estimated start index, travel direction is inferred from an initial
arc, backward values are held by the monotonic validator, and a large drop near the
end is converted to 100%. This explains the observed saturation mechanism, but it
does not yet prove which initial projection or detection error is the root cause.
The next implementation must reproduce and instrument the failure before selecting
a fix.

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

The active `TelemetryPipeline`, CSV export, and API-facing data still use legacy
records without field-level quality or anomaly output. Quality propagation is
therefore an implemented contract in isolation, not an end-to-end capability.
Holding a value must never make it indistinguishable from a fresh observation.

## Reliability stage gates

### Priority 1 — trustworthy `s` anchor and progression

Required work:

1. reproduce the 2026-09-01 failure with a focused regression;
2. expose raw projection, anchor, direction, validation decision, and output quality;
3. identify and correct the root cause rather than tuning thresholds blindly;
4. replay the controlled Spa evidence.

Exit criteria:

- `s` does not enter the completion band before the real start/finish crossing;
- `s` restarts near zero only at a confirmed new lap;
- forward progress remains coherent without hiding long invalid plateaus;
- known Spa passages map to stable `s` ranges across repeated laps;
- missing, held, or low-confidence position is explicit.

### Priority 2 — robust lap transitions

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

## Review gate

No technical implementation plan is active yet. The repository documentation must be
reviewed with Loïc first. After that review, create one detailed, test-driven plan for
the three ordered reliability priorities and link it from `docs/current-status.md`.
