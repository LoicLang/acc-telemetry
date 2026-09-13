---
summary: approved generic design for longitudinal position using speed odometry, visual map projection, temporal fusion, and trusted lap anchors
read_when:
  - implementing or reviewing the production correction for s
  - changing speed integration, map centerline extraction, red-dot tracking, or lap anchoring
  - deciding how position quality and uncertainty reach analysis
---

> Historical evidence only — archived13 September2026. Old instructions, gates and next actions below are not current. Follow [current status](../../current-status.md).

# Generic `s` fusion design

## Decision

Build a circuit-generic longitudinal position estimator and validate it on Spa first.
The production output is a fusion of two independently inspectable signals:

- `s_odometry`: progress predicted from integrated vehicle speed;
- `s_visual`: absolute position candidates derived from the static full-map minimap;
- `s_fused`: the selected coaching coordinate after temporal fusion and trusted lap
  anchoring.

The algorithm must not contain Spa-specific coordinates, corner definitions, or
track templates. Spa is the first validation dataset because it currently provides
the strongest evidence: native 1080p, 14 detected boundaries, 139,561 diagnostic
rows, and repeatable laps.

## Problem statement

The existing map-only `s` is invalid for three confirmed reasons:

1. geometric start detection selects the wrong point;
2. the thick white map line is represented by a double contour, so adjacent pixels
   can map to distant path indexes;
3. red-dot detection chooses the largest red region before validating it, so red
   cockpit or scenery hides the smaller valid car dot.

The monotonic hold and forced-completion rules then amplify and conceal those
upstream failures. A threshold-only correction cannot solve the problem.

## Options considered

### Option A — repair the current contour tracker

Keep the double contour, select plausible red objects, restrict index search around
the previous index, discard the geometric anchor, and remove forced completion.

This is the smallest code change, but the path remains physically ambiguous. Close
track sections, contour thickness, and a one-pixel dot movement can still create
topological mistakes. This option is useful only for short-lived experiments.

### Option B — use speed integration alone

For each interval:

```text
delta_distance_m = speed_kmh / 3.6 * delta_time_s
distance_m += delta_distance_m
```

A completed offline lap can be normalized as:

```text
s_odometry(t) = cumulative_distance(t) / total_integrated_lap_distance
```

This is generic, monotonic, independent of minimap geometry, and valuable as an
immediate baseline. It is not sufficient as the only production coordinate because
speed errors accumulate, actual racing-line length differs between laps, pit lanes
and off-track travel distort distance, and there is no absolute visual correction
inside a lap.

Official circuit length must not be the primary denominator. It follows a track
measurement convention and differs from the path actually driven. It may be used as
an optional sanity bound when track metadata is known.

### Option C — fuse odometry and a unique visual path — selected

Create a single centerline from the static map, retain all plausible red-dot
candidates, use `v * delta_t` to predict expected progress, and choose or reject visual
candidates against that prediction and recent 2D motion.

This directly resolves the measured `1905 -> 370` ambiguity: when two visually close
branches imply 1.5% and 34.7%, the candidate compatible with odometric prediction and
temporal continuity wins. Visual observations correct odometric drift; odometry
bridges missing visual observations.

This approach is generic across static full-map circuits and preserves explainable
evidence for every output.

## Architecture

### 1. Raw observations

Extraction produces observations without silently deciding truth:

- timestamp and frame number;
- speed value plus field quality;
- raw lap-number OCR observation;
- confirmed lap boundary plus confidence;
- every red contour that passes basic size, shape, color, and centroid checks;
- static white-map probability or mask.

The current behavior of selecting the largest red contour and discarding the frame
when it is invalid is removed. Invalid large regions remain rejected individually;
smaller plausible candidates remain available.

### 2. Visual centerline

The stable white-map mask is reduced to a one-pixel centerline rather than an external
outline. Short branches such as start-line markers are pruned. The retained closed
cycle is ordered and resampled at stable arc-length intervals.

The implementation must detect and report invalid topology:

- no closed cycle;
- multiple unresolved cycles;
- excessive branches;
- discontinuous or implausibly short path.

It must not silently fall back to the old external contour.

### 3. Odometric progress

For each valid speed interval:

```text
delta_distance_m = speed_kmh / 3.6 * delta_time_s
```

The estimator retains cumulative distance, uncertainty, and speed quality. Missing or
anomalous speed does not become observed distance. Short gaps may use an explicitly
interpolated estimate; uncertainty increases with gap duration.

For an offline completed clean lap, `s_odometry` is normalized by that lap's total
integrated distance. Across several clean laps, the median integrated distance becomes
`effective_lap_length_m`, used for online prediction and sanity checks. It is a learned
session/track calibration, not a replacement for raw per-lap distance.

### 4. Temporal visual projection

Every plausible red-dot candidate is projected onto the ordered centerline, possibly
yielding several nearby path candidates. Candidate scoring considers:

- distance from the red centroid to the centerline;
- 2D displacement from the last accepted dot;
- wrapped progress difference from odometric prediction;
- maximum physically plausible progress from speed and elapsed time;
- current uncertainty.

The estimator accepts a visual correction only when one candidate wins by a defined
margin. Ambiguous observations remain ambiguous; they are not converted to false
certainty.

### 5. Fused state

The state contains:

```text
s_fused
s_odometry
s_visual (optional)
distance_m
effective_lap_length_m
uncertainty
source: observed | fused | predicted | interpolated | missing
reasons[]
```

When visual evidence is reliable, it corrects drift smoothly. During a short visual
gap, odometry predicts progress and quality is not `observed`. During a long or
high-uncertainty gap, `s_fused` becomes unavailable rather than being held forever.

The current unconditional backward hold and forced-completion behavior are removed
after upstream fusion is proven.

### 6. Trusted lap anchoring

`s` resets to zero only on a confirmed lap boundary. Geometric top-of-map heuristics
never define the origin.

Before the first confirmed boundary, samples are marked unanchored. Because processing
is offline, the pipeline may rebase a preceding complete captured lap in a second pass
only when both boundaries and the full sequence are known. It must not claim that a
partial opening lap starts at zero.

A low-confidence OCR change cannot reset position. The lap-boundary contract therefore
links this work to the separate robust-transition priority: raw OCR and confirmed lap
state remain distinct.

## Data flow

```text
video frames
  -> speed observation + quality
  -> red candidate observations
  -> confirmed lap boundaries
  -> static map centerline

speed observations
  -> integrate v * delta_t
  -> s_odometry + uncertainty

red candidates + centerline + s_odometry prediction
  -> temporal candidate selection
  -> s_visual correction

s_odometry + s_visual + confirmed boundary
  -> s_fused + source + uncertainty + reasons
  -> normalized TelemetrySample
  -> future corner analysis
```

## Implementation sequence

The next agent must produce a detailed TDD plan before changing behavior. The planned
slices are:

1. `s_odometry` baseline on synthetic traces and clean Spa laps;
2. plausible red-candidate extraction that survives large red backgrounds;
3. unique map centerline extraction with topology validation;
4. odometry-constrained temporal projection;
5. trusted lap anchoring and removal of the geometric origin;
6. fused quality/uncertainty at the analysis boundary;
7. replay on the clean BMW session, then the crash-heavy secondary session;
8. only then reevaluate smoothing and completion logic.

Each slice is an atomic tested commit. No corner segmentation work belongs in this
milestone.

## Spa validation

Spa validates the generic algorithm without contributing special-case code.

Required evidence:

- compare `s_odometry`, `s_visual`, and `s_fused` independently;
- no entry into the completion band before a confirmed boundary;
- no reset without a confirmed boundary;
- adjacent red-dot pixels do not produce nonlocal path jumps;
- known physical checkpoints align across clean laps within a documented tolerance;
- short missing-dot gaps remain predicted/interpolated and explicit;
- long gaps become unavailable rather than silently observed;
- crash/off-track laps expose degraded confidence and do not recalibrate effective
  lap length;
- legacy 720p recordings remain readable through their existing profile.

Initial quantitative target for repeated clean checkpoints: `s_fused` spread no worse
than 0.2 percentage point across comparable laps. This is a validation target, not a
hard-coded runtime threshold.

## Non-goals

- no Spa-specific map or corner coordinates;
- no per-circuit template library in the first implementation;
- no official circuit length as mandatory input;
- no machine-learning model or opaque score;
- no lateral coordinate `d`;
- no corner segmentation, coaching diagnosis, or dashboard;
- no silent fallback from failed fusion to the legacy saturated value.

## Review and stop conditions

If centerline topology cannot be made unambiguous on Spa without circuit-specific
rules, stop and compare two alternatives before continuing:

1. use a clean-lap red-dot trajectory to order the generic map graph;
2. introduce a versioned per-track reference centerline registered to the HUD map.

Do not add a fourth heuristic patch to the old contour tracker.
