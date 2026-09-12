---
summary: owner-clarified automatic full-video trial with annotations used only for subsequent numerical validation
read_when:
  - running a complete video without annotation-gated extraction
  - interpreting run-024 continuous curves and scoped quality measurements
---

# Extract the whole video, validate on annotated zones

Owner clarification, 12 September 2026: run-023 was not the intended experiment.
Its sparse annotation gate suppressed nearly all useful data. The requested test is
**automatic extraction of a complete existing video, followed by quality checks only
where reference annotations exist**. Run-024 completes that experiment. Gate A remains
FAIL; B/R remain blocked. No fresh recording was required for this demonstration.

## Inspect the result

Open `data/lab/coaching-reliability/run-024/reports/index.html` directly, or serve
run-024 locally and visit `/reports/index.html` (live preview on127.0.0.1:8766).
The simplified report displays three continuous curves with reference annotations
as black crosses, error tables, estimated progress and four reused video excerpts.
`reports/continuous.html` opens the complete curves alone; `processed/crash-session/`
contains the original telemetry-v2 manifest, observations, samples and CSV.
The actual CLI report is also retained in `reports/telemetry_interactive_*.html`.
The simpler presentation uses the same exported values without smoothing or filling.

All paths below are relative to ignored run-024. `reports/command.json` records the
exact CLI invocation; `run.py`, `evaluate.py`, `publish.py` and `verify_final.py`
record local reproduction. Use a fresh run directory, never overwrite frozen runs.
Personal video, full telemetry, generated reports and OCR assets remain ignored.

## Explicit automatic mode and provenance

CLI: `--measurement-mode automatic`; web Python service:
`process_video(..., measurement_mode="automatic")`. Both use the same modern
`TelemetryPipeline`. The `reviewed` default and historical behavior remain available.
HTTP forms retain that default; no upload form or deployment was added.

Automatic mode rejects visibility annotation inputs. The same fresh speed and control
readers run on every frame; numerical speed admission keeps its existing settings.
There is no synthetic full-source visibility review, interpolation of measured speed,
legacy median, pedal smoothing, rescaling to100% or threshold search. Empty/black ROI,
invalid text and rejected speed remain missing. TC/ABS remain unsupported.

Values may be `observed` because they are fresh machine readings; this does **not**
mean verified accuracy or reviewed HUD visibility. Available values retain
`speed_hud_unverified` / `hud_visibility_unverified`; derived progress retains
`automatic_measurements_unverified`. The manifest records the mode in resolved
configuration, its measurement fingerprint includes that configuration, and coaching
eligibility remains false. CSV, normalized samples and web data preserve reasons;
web session metadata also records the mode. This does not qualify a HUD detector:
a plausible reading on the wrong HUD can still be wrong outside the annotated scope.

## Actual complete-source result

Same immutable incidents source as run-023, SHA-256
`b2558ba17c174043e94345f240b31614f4a428246cc437ac09537d37156b7124`,
453613415 bytes. Native1920×1080, exactly60fps CFR preflight passed before extraction.
All **29402 presented frames / 490.033s** were processed, with passing final decode
coverage and exact PTS/frame alignment. No annotations were supplied to extraction.

| Signal | Available /29402 | Coverage, not accuracy |
| --- | --- | --- |
| Speed |29298|99.65%|
| Brake |29402|100%|
| Throttle |29402|100%|
| Raw counter |29402|100%|
| Gear |28913|98.34%|
| Steering |29232|99.42%, numerical accuracy untested|
| Fused progress `s` |26844|91.30%, spatial accuracy untested|
| Odometric / visual `s` |29383 /26462|estimated components|
| TC / ABS |0|unsupported|

The104 absent speed readings retain reasons:95 empty OCR,5 rate refusals,3 out of
range and1 invalid text. All29402 raw speed OCR strings are byte-for-byte unchanged
versus run-023. The1366 pedal readings in the previously reviewed cells (683 per
channel) are numerically unchanged. No held/interpolated/predicted speed or pedals
are published. Internal bounded odometry interpolation retains separate provenance.

Progress is now available because the full automatic speed series reaches calibration
and fusion. Availability is not independent spatial accuracy; no meter-error or
coaching claim follows. The report shows the estimate and its missing intervals.

## Quality checks only against existing annotations

Both the existing `scripts/validate_capture.py` and the run's direct comparison read
the new artifact after extraction. Original annotations/reviewers/approvals remain
unchanged. No new numerical labels, exhaustive review, agents or holdout inspection.

| Field | Available annotated points | MAE | P95 | Maximum absolute error |
| --- | --- | --- | --- | --- |
| Speed, km/h |21/21|0.00|0.00|0.00|
| Brake, percentage points |21/21|1.60|5.62|5.88|
| Throttle, percentage points |21/21|3.12|5.88|5.88|

On the18 existing visibility segments /683 frames, speed is available679/683 and each
pedal683/683. Segment V-CRASH-15 remains28/31 (90.32%); do not substitute the aggregate
for this local limitation. These segments provide visibility/availability evidence,
not dense numerical ground truth. The21 numerical points do not validate every frame.

The main observed pedal limitation persists: full throttle often reads94.12%, and
released signals can leave0.65–1.70%. Do not infer insufficient full throttle or a
voluntary overlap from these differences. At the known impact, correct39km/h following
66→39 remains rejected by the unchanged rate policy. No tuning on this incident.

The frozen run-022 full counter labels match **29402/29402 fresh observations and
4/4 transitions**, with zero missed/extra events. Candidate/confirmation times and
source-frame alignment are unchanged. L2 timer-reset truth remains distinct from
numeric counter truth. No BMW replay was necessary for this corrected experiment.

Evidence: `reports/results.json`, `annotated-validation.json`, `preflight.json`,
`preservation.json`, `pipeline.log`; final tests, hashes and browser inspection:
`reports/final-verification.json`. The standard validator's fingerprint is compatible
with this automatic extraction configuration; no old acceptance result transfers.

## Verification and next action

Five new regression tests cover explicit automatic reads, black/absent/invalid
abstentions, unsmoothed pedal changes, pipeline/artifact provenance, invalid modes,
annotation-input rejection and CLI/web wiring. Default reviewed-mode regressions stay
green. 32 focused tests and323 full-suite tests pass; logs are recorded with the final verification.
The complete and braking charts were opened in the app; the reference crosses and
continuous measurements are visible. Sources, run-023 and earlier labels are preserved.

**Next action:** reserve the later distinct independent native1080p60CFR recording
under frozen extractor/settings before inspection, then use the same extraction-first,
annotation-validation workflow. No exhaustive review of these development recordings
is needed to inspect the delivered trial; Gate A still blocks reliable coaching.
