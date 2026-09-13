---
summary: approved generic design for robust red-dot candidates and confirmed-boundary visual-anchor recovery
read_when:
  - changing red-dot shape acceptance or confirmed-boundary visual anchoring
  - implementing or reviewing the missing-boundary-dot correction
---

> Historical evidence only — archived13 September2026. Old instructions, gates and next actions below are not current. Follow [current status](../../current-status.md).

# Generic boundary visual-anchor design

## Decision

Repair the missing-boundary-dot failure in two independent layers:

1. retain compact red-dot contours whose compressed outline is irregular but whose
   relative size and shape remain plausible;
2. when a confirmed lap boundary still has no viable exact projection, reconstruct
   its visual anchor from bounded viable projections immediately around it.

The lap confirmer remains the only authority that can anchor or reset fused progress.
Nearby visual evidence supplies only the raw centerline coordinate of an already
confirmed boundary.

## Confirmed problem

The new BMW replay confirms a boundary at 286.3667 seconds. The current red-candidate
filter accepts a viable observation at 286.3000 seconds, rejects the next five frames,
and accepts one again at 286.4000 seconds. The exact boundary frame therefore has no
candidate and `ProgressSessionEstimator` never initializes `raw_anchor_s` for the
following lap.

Direct OpenCV inspection of the source frames shows that the red dot remains visible,
has a stable 16 by 16 pixel bounding box, and has a valid area fraction. Compression
and overlap with the white map stroke make its raw contour perimeter irregular:

- configured minimum circularity: 0.35;
- rejected boundary-window circularity: 0.270 to 0.318;
- accepted following-frame circularity: 0.431.

This is not a lap-number OCR failure. The OCR observations correctly produce one
confirmed `0 -> 1` transition. OCR identifies when a lap changes; it cannot identify
the corresponding raw coordinate on the visual centerline.

At one-second sampling across the three 1080p validation sessions, a preliminary
compact-shape characterization produced this evidence:

| Session | Sampled frames | Current zero-candidate frames | Zero-candidate frames after characterization |
| --- | ---: | ---: | ---: |
| New BMW | 794 | 41 | 0 |
| Clean control | 316 | 8 | 1 |
| Crash control | 491 | 34 | 31 |

The clean sessions justify improving candidate retention. The remaining crash-session
gaps show why detection alone cannot be the complete correction.

## Options considered

### Detection-only correction

Relax the contour-shape rule and otherwise keep exact-frame anchoring unchanged.

This addresses the measured clean-session cause, but a real occlusion, HUD transition,
or undecodable frame can still coincide with a confirmed boundary and lose a full lap.

### Temporal-anchor-only correction

Keep the current circularity rule and always recover a boundary anchor from a nearby
accepted projection.

This bridges the measured gap, but preserves avoidable false negatives throughout
the session and makes temporal recovery carry more load than necessary.

### Layered candidate retention and bounded recovery — selected

Retain compact imperfect contours first, then reconstruct an anchor only when exact
viable visual evidence remains unavailable. Each layer has one responsibility and
can be tested independently.

## Candidate-retention rules

`extract_red_candidates()` continues to return evidence rather than choose truth.
Every contour must pass the existing dual-HSV red mask and configured relative-area
range. It then passes the shape gate through either path:

1. its raw contour circularity meets the existing minimum; or
2. its bounding-box aspect ratio, filled extent, and convex compactness meet new
   validated configuration thresholds.

Use these initial dimensionless thresholds, derived from the measured boundary
windows and subject to all three replay gates:

```text
minimum bounding-box aspect ratio = 0.75
minimum filled extent             = 0.45
minimum convex compactness        = 0.45
```

Aspect ratio is `min(width, height) / max(width, height)`. Filled extent is contour
area divided by bounding-box area. Convex compactness is
`4 * pi * contour_area / convex_hull_perimeter**2`; retaining the original contour
area continues to penalize concavity while the hull perimeter removes compression
jaggedness from the boundary-length estimate.

The second path admits a compact dot with a jagged or partially overwritten outline.
It must continue to reject elongated bars, sparse fragments, large cockpit regions,
tiny specks, and zero-moment contours. Thresholds are dimensionless and validated in
configuration; no absolute dot size, circuit coordinate, car model, or track shape is
allowed.

Relaxed extraction does not make a contour an accepted position. Existing projection
and temporal selection remain responsible for truth:

- the candidate must project within the ROI-relative centerline-distance gate;
- its wrapped progress must agree with odometric prediction and uncertainty;
- its image displacement must remain temporally plausible;
- one candidate must win by the configured score margin;
- ties and nonphysical candidates remain unavailable with explicit reasons.

## Boundary-anchor recovery

For every confirmed boundary, choose its raw visual anchor in this order:

1. an unambiguous viable projection on the exact boundary frame;
2. an odometry-weighted interpolation between viable projections bracketing the
   boundary;
3. the nearest viable one-sided projection when it satisfies stricter time and
   odometric-distance limits;
4. no visual anchor when none of the above is trustworthy.

Recovery is evaluated offline because the current production pipeline already
collects raw observations before finalizing progress.

Use these initial dual recovery gates:

```text
bracketing maximum gap from boundary = 0.25 seconds and 0.005 normalized odometry
one-sided maximum gap from boundary  = 0.10 seconds and 0.002 normalized odometry
```

Both limits must pass. Seconds make the rule independent of frame rate; normalized
odometry prevents a high-speed or short-circuit case from accepting a visually stale
anchor. These are validated configuration values, not literals in fusion code.

### Bracketing interpolation

Let `before` and `after` be the closest compatible viable projections on either side
of a confirmed boundary. Both must fall inside configured maximum time and normalized
odometric-distance gates, and the pair must be mutually consistent with short forward
motion.

Calculate the boundary position along the shortest wrapped centerline interval. Weight
the interpolation by odometric distance, falling back to elapsed time only when the
bounded interval contains no usable distance increment:

```text
ratio = distance(before, boundary) / distance(before, after)
anchor_raw_s = wrap01(before.raw_s + wrapped_delta(after.raw_s, before.raw_s) * ratio)
```

This handles a start/finish interval such as `0.998 -> 0.002` without interpolating
through the opposite side of the circuit.

### One-sided recovery

If only one viable projection exists inside the recovery window, use it only under a
stricter maximum time and normalized-distance gate. Prefer a previously established
centerline direction to transport the projection to the boundary. If direction is not
yet known, retain the nearest raw coordinate with uncertainty proportional to its
bounded distance from the boundary.

One-sided recovery is deliberately less trusted than interpolation and must never be
allowed outside the configured short-gap limits.

## Authority and safety invariants

- Only `ConfirmedLapBoundary` may create or reset an anchor.
- A raw OCR change, visual wrap, point near the map origin, or recovered projection
  cannot create a boundary.
- A recovery search cannot cross another confirmed boundary.
- Exact evidence always wins over recovered evidence.
- Multiple plausible recovery paths without a clear margin yield no anchor.
- Failure remains safe: progress may stay unavailable; it never falls back to the
  legacy held or forced-completion tracker.
- Opening partial laps remain unanchored.
- Calibration continues to use only accepted complete boundary-to-boundary laps.

## Provenance and uncertainty

Expose stable boundary-anchor provenance in diagnostic results and reasons:

- `boundary_anchor_exact`;
- `boundary_anchor_interpolated`;
- `boundary_anchor_nearest`;
- `boundary_anchor_missing`.

Add `boundary_anchor_source` to `ProgressFrameResult` and to the ignored diagnostic
trace schema. Preserve the existing production telemetry and legacy CSV/API columns;
this correction does not expand their compatibility contract. The boundary frame's
reasons include the same stable provenance value.

Exact anchoring has the existing baseline uncertainty. Interpolated anchoring adds
uncertainty from the two projection scores and the bounded gap. One-sided anchoring
adds a larger penalty based on elapsed time and normalized odometric distance. The
uncertainty feeds existing fusion behavior; it is not silently promoted to observed.

## Component boundaries

- `extraction/map_progress.py` owns dimensionless contour-shape evidence only.
- `application/progress.py` owns viable projection selection, boundary association,
  interpolation, provenance, and uncertainty.
- `application/config.py` and `config/telemetry.yaml` own all new validated thresholds.
- The lap confirmer, odometry integration, domain progress contract, CLI, and web
  adapters retain their current responsibilities.

No detector may import lap state, and no lap-state code may inspect OpenCV data.

## TDD acceptance cases

Write focused RED tests before each behavior change:

1. a compact irregular red contour fails the old circularity-only gate and is retained
   through the new shape path;
2. elongated, sparse, oversized, undersized, and non-red artifacts remain rejected;
3. multiple retained candidates still require projection and temporal disambiguation;
4. an exact boundary projection is preferred and reports `boundary_anchor_exact`;
5. missing exact evidence with viable before/after projections interpolates the raw
   anchor using odometric distance;
6. interpolation across `0.998 -> 0.002` produces an anchor near zero;
7. a sufficiently close one-sided projection is accepted with higher uncertainty;
8. distant, mutually inconsistent, ambiguous, or cross-boundary projections produce
   `boundary_anchor_missing`;
9. no projection or raw OCR observation can reset progress without a confirmed
   boundary;
10. the complete following lap emits fused progress instead of remaining unavailable.

## Real-capture validation

After focused and full automated tests pass, replay in this order:

1. new BMW session `/Users/loiclang/Movies/2026-09-03 22-42-08.mov`;
2. clean representative control;
3. crash-heavy representative control.

The new BMW replay must retain four confirmed boundaries, three accepted calibration
laps, zero unconfirmed resets, zero nonlocal jumps, and zero premature completions.
Its first complete lap must no longer remain unavailable because of the missing exact
boundary candidate. Record candidate/source counts, anchor provenance, unavailable
duration, effective length, and checkpoint spread.

Both controls must retain their existing safety gates. A correction that improves the
new BMW session but regresses clean checkpoint spread, admits nonlocal jumps, changes
crash-lap calibration, or creates an unconfirmed reset is rejected.

All videos, frames, traces, and JSON reports remain ignored local evidence.

## Non-goals

- no OCR threshold or lap-confirmation change;
- no Spa coordinate, circuit template, or car-specific crop;
- no global lowering of circularity without complementary shape constraints;
- no corner segmentation or coaching work;
- no change to legacy CSV/API compatibility;
- no online/live estimator redesign in this correction.
