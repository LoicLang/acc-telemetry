---
summary: run-023 full incidents CLI trial, visible report, bounded video checks and corrected misleading pedal fills
read_when:
  - opening or reproducing the complete incidents demonstration
  - assessing current signal usefulness, missing data or the time-report fill correction
---

# Complete incidents demonstration — run-023

This reviewed-mode trial is superseded for the owner’s intended experiment by
[run-024 automatic extraction](automatic-system-trial.md). Run-023 remains the
frozen diagnostic explaining the sparse annotation gate and display correction.

Delivered 12 September 2026 on `codex/coaching-reliability`. This is a development
trial, **not independent acceptance. Gate A FAIL; B/R remain blocked.**

## Open the result

Local entry: `data/lab/coaching-reliability/run-023/reports/index.html`.
It includes the corrected production report, coverage/progress explanation, four
native 1080p60 video excerpts, the same renderer's window reports and source/HUD images.
Open the HTML directly, or serve run-023 locally and visit `/reports/index.html`.
The live demonstration uses `http://127.0.0.1:8765/reports/index.html`.
No remote publication of personal media is needed.

Full chart: `reports/telemetry_corrected.html`; artifact:
`processed/crash-session/` (manifest, observations, normalized samples and CSV).
The original CLI `telemetry_interactive_20260912_173339.html` remains a **diagnostic
with misleading pedal fills**, preserved to explain the correction below.
`reports/results.json`, `bmw-reuse.json`, `windows.json`, `preflight.json`,
`command.json` and `pipeline.log` hold exact inputs, checks and invocation.
All run-relative paths in this document refer to ignored run-023.

## Complete processing and reuse

The actual `main.py` CLI ran `TelemetryPipeline`, also used by the web Python
service, over the complete existing `crash-representative.mov`. Source SHA-256:
`b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124`;
size 453613415 bytes. Preflight verified native 1920×1080, exactly 60 fps CFR before
processing; final decoded coverage and PTS pass: **29402/29402 presented frames**,
8 min 10.033 s. The container's 29416 nominal frame count exceeds the verified presented-frame count by 14;
it is not the presented-frame denominator. No upscaling/resampling or source edit.

Inputs: existing run-008 source-associated control review (path/hash in preflight)
and run-014 `processed/crash-speed-visibility-canonical.json`. No review extended,
no new exhaustive annotation, no agent, no threshold experiment and no OCR replay
for BMW. Frozen run-021/022 labels and other consumed evidence are unchanged.

- Incidents full pipeline: **29402/29402 raw counter observations exact and fresh**
  against run-022;4/4 events, no missing/extra events. Candidate times 0.250,146.350,
  294.800,472.650s; confirmation 66.7 ms later. P95 midpoint error 8.3 ms.
- BMW preserved run-015 artifact: automatic comparison against run-021 again gives
  **47589/47589 exact fresh observations and4/4 events**. No new BMW processing.
- There are three complete intervals between incidents counter changes:146.100,
  148.450,177.850s; opening lap3 and final lap7 are partial. These are counter-derived
  intervals, not independent physical crossing truth. Report separators use confirmation.

## Useful output and concrete limitations

| Signal | Available /29402 | Whole-video coverage |
| --- | --- | --- |
| Speed |679|2.31%|
| Brake |683|2.32%|
| Throttle |683|2.32%|
| Raw counter |29402|100%|
| Gear |28913|98.34%|
| `s`, odometry `s`, visual `s` |0 each|0%|
| Steering, TC, ABS |0 each|0%|

The pipeline processed every image; reviewed visibility admits measurements only
in sparse spans. No complete incidents lap is calibrated. Map extraction succeeds,
but does not supply usable progress by itself. Whole-lap analysis, position comparison
and a continuous braking debrief remain unavailable. Missing is not zero or held speed.

Speed matches all 21 preapproved numerical points exactly. All 683 previously reviewed
speed frames match the frozen run-014 admission result:679 values and4 abstentions.
At 349.8667 s, a correct 39 after a real 66→39 drop is rejected by the existing rate rule;
other abstentions retain raw 698, 4, 638. No tuning was done on this known incident.

On 21 approved points per pedal, brake/throttle MAE is 1.60/3.12 percentage points;
maximum error 5.88 points each. Full throttle often reads 94.12%, and released inputs
can leave 0.65–1.70%. Do not infer failure to reach full throttle or voluntary overlap
from these small differences. No artificial rescaling to 100%, smoothing or causal
interpretation was added. These scoped checks do not establish full-video accuracy.

## Bounded source/report comparison

Primary inspected 18 selected native source frames with scene context/HUD crops;
four short playable excerpts are included. This is not exhaustive annotation, a new
visibility input or a precise onset-latency benchmark.

| Window | Source observations and displayed result |
| --- | --- |
| Braking186–191s |260→223→191→120km/h at187,188,188.5,190s agree; attack and later release appear in the graph. Downshift throttle spikes remain intact. Coverage178/300 images; gap188.767–189.750s prevents a complete release trace.|
| Acceleration93–99s |128,132,137km/h at94,96,98s agree. Approximate visual throttle100/58/85 versus94.12/55.56/79.74. Coverage93/360; visible137 at98.5s correctly remains missing outside the existing review.|
| Incident347–352s |Gravel excursion, rotation and wall proximity;103/89/38km/h at348/349/350s agree. Brake at350s reads94.12 versus visually full. Speed89/300, pedals93/300; visible16 at351s remains missing outside review.|
| Lap0–1s |Timer reset frame11, counter3→4 frame15, confirmation frame19. Raw counter follows the actual new digit; the report separator is66.7ms later. Speed/pedals40/60; no physical crossing claim.|

## Demonstrated display defect and bounded correction

Opening the actual CLI report exposed large green/red filled polygons across long
null intervals. Plotly `fill='tozeroy'` bridges those gaps even when the measurement
line itself breaks. This materially suggested pedal coverage that did not exist.

A focused RED test reproduced the unsafe fill in both time-report layouts. The
renderer now uses unfilled pedal lines and explicitly disables gap connection.
Only visualization changed; extraction, normalization, numerical settings, pedal
values and the published session are unchanged. Reports were regenerated from the
existing CSV, without rerunning video/OCR. Browser inspection confirms the phantom
areas disappear and the braking window retains its abrupt changes and missing span.
The companion document supplies coverage/progress context absent from the base chart.

Verification: 33 focused tests and318 full-suite tests pass; the original 32 focused
and 317 full tests also passed before the display correction. Initial focused invocation
failed two imports because it omitted `tests` from PYTHONPATH; corrected invocation
passes. RED/GREEN, full-suite, docs discovery, source/input/module preservation and
artifact hashes are under `reports/`; see `final-verification.json`.

**Next action:** reserve a distinct independent native 1080p60 CFR recording under
frozen extractor/settings **before inspecting it**. Do not reuse the historical
holdout as independent or reopen an exhaustive campaign on these development videos.
