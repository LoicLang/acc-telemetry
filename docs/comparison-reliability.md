---
summary: A5 bounded comparison rules, nullable provenance-preserving API and verified client limitations
read_when:
  - comparing partial or degraded laps
  - consuming the comparison API or Plotly position report
  - implementing A6/A7 admission gates for estimated progress
---

# Comparison without invented coverage

`analysis/alignment.py` owns interpolation and common-position time differences.
No OpenCV, FastAPI or Plotly dependency belongs in that module. The existing Plotly
position comparator delegates to it; the HTTP comparison endpoint returns original
frame evidence rather than resampling it on the server.

The default limits in `config/telemetry.yaml` are:

- `comparison.max_position_gap_s: 0.005`, in normalized longitudinal **s**, not seconds;
- `comparison.max_time_gap_s: 0.10`, in seconds between adjacent source observations.

Both are validated, including finite values. The existing fusion unavailable-
uncertainty threshold supplies the local progress uncertainty bound.

The algorithm keeps original temporal order. It splits before removing missing,
nonfinite, held or anomalous values and before backward movement or long time/position
gaps. Repeated positions have no unique passage time and are excluded; overlapping
forward runs make shared targets ambiguous. There is no sorting to repair reversals,
no extrapolation beyond a partial lap, and no interpolation across a rejected row.

Each channel retains its own coverage, run IDs and output quality. Direct legacy
values without provenance remain `legacy_unverified`; interpolated values are marked
`interpolated`. The diagnostic report can inspect legacy data but does not admit it
for coaching. Strict `coaching=True` requires observed field provenance and trusted
caller gate approval for fused/predicted/interpolated progress, together with local
uncertainty checks. A CSV field cannot grant that approval. An explicit anomalous
position hint overrides a plausible progress source. No real gate approval exists yet.

Pairwise plots mask each channel to common admitted coverage. Null separators stop
Plotly from connecting different runs, even when the gap is narrower than the output
grid. Delta is `(time_a - confirmed_start_a) - (time_b - confirmed_start_b)` on common
positions. The existing record reason `lap_boundary_confirmed` identifies a unique
confirmed start, including when progress is missing at that frame. No unique start
means no delta; the first surviving observation is never substituted for the start.
Raw comparison files without boundary evidence remain usable for bounded diagnostic
curves but do not acquire an invented lap-time origin or coaching eligibility.

## HTTP and consumer contract

`POST /api/telemetry/compare` retains all six `s_*` fields, `quality_hint`, field reasons,
raw lap labels, speed/gear raw values and additional record fields. Throttle, brake,
steering, TC and ABS are nullable. Source CSV OCR strings retain leading zeros and
literal symbols. Dictionary endpoints continue returning their complete evidence.
`GET /api/telemetry/{video}/summary` uses the corrected packaged visualizer import.

Consumers must render null as unavailable, not zero, and honor quality before analysis.
Tests cover the real endpoint functions, declared response serialization and generated
Plotly trace data/line breaks. A manual local Uvicorn/curl smoke also verified both
comparison and summary routes returned HTTP 200 and retained provenance/nulls.
Evidence is ignored under `data/lab/coaching-reliability/run-001/a5-http-*`.

The React frontend mentioned in `QUICKSTART_WEB.md` is absent from this checkout;
there are no tracked JS/TS client sources to run. No compatibility claim is made for
that external/older UI. Verified current consumers are the API and repository Plotly
reports. No frontend dependency was installed or substituted.

A0–A5 close the audited software paths. A6/A7 must still annotate actual video and
measure error/coverage independently before gate A can pass. None of these comparison
rules establishes spatial accuracy in metres or validates a driving recommendation.
